import os
from typing import Any, Dict, Optional

import requests
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from .models import (
    Arbitration,
    ChangeScope,
    Claim,
    ClaimSeverity,
    Conflict,
    ConflictChoice,
    ConflictReasonCode,
    GateCheckResult,
    ScopeType,
)

app = FastAPI()

_claim_store: dict[str, Claim] = {}

DEFAULT_PROMPT_TEMPLATE = (
    "You are a custodian AI.\n\n"
    "Your job:\n"
    "- Detect scope creep\n"
    "- Detect violations of user preferences\n"
    "- Detect large or risky changes\n"
    "- Keep feedback short\n\n"
    "User rules:\n"
    "- Do not expand scope unless explicitly asked\n"
    "- Avoid inventing architecture\n"
    "- Prefer small, boring solutions\n"
    "- Avoid large diffs or multi-file rewrites\n"
    "- Prefer removal over deprecation\n"
    "- Do not preserve backward compatibility unless explicitly requested\n"
    "- Do not leave dead, unused, or obsolete code behind\n"
    "- Favor the cleanest correct design over incremental compatibility\n"
    "- If something feels heavy, flag it\n\n"
    "Plan to review:\n"
    "{{PLAN}}\n\n"
    "Respond with:\n"
    '- "OK" if no issues\n'
    '- Otherwise: "RED FLAGS:" followed by bullets\n'
)


def build_prompt(plan_text: str, prompt_template: Optional[str]) -> str:
    template = prompt_template or DEFAULT_PROMPT_TEMPLATE
    if "{{PLAN}}" not in template:
        raise ValueError("Prompt template missing {{PLAN}} placeholder")
    return template.replace("{{PLAN}}", plan_text)


def extract_text(payload: Dict[str, Any]) -> str:
    return payload["output"][0]["content"][0]["text"]


def extract_diagnostics(payload: Dict[str, Any]) -> Dict[str, Any]:
    usage = payload.get("usage") or {}
    diagnostics: Dict[str, Any] = {
        "model": payload.get("model"),
        "total_tokens": usage.get("total_tokens"),
        "input_tokens": usage.get("input_tokens"),
        "output_tokens": usage.get("output_tokens"),
        "created_at": payload.get("created_at") or payload.get("created"),
    }
    return {k: v for k, v in diagnostics.items() if v is not None}


def register_claim(claim: Claim) -> Claim:
    if claim.claim_id in _claim_store:
        raise HTTPException(status_code=400, detail="claim_id must be unique")
    _claim_store[claim.claim_id] = claim
    return claim


def _filter_claims(scope: ChangeScope) -> list[Claim]:
    if not any([scope.repo, scope.path, scope.subsystem, scope.api]):
        return list(_claim_store.values())

    scope_types: set[ScopeType] = set()
    if scope.repo:
        scope_types.add(ScopeType.REPO)
    if scope.path:
        scope_types.add(ScopeType.PATH)
    if scope.subsystem:
        scope_types.add(ScopeType.SUBSYSTEM)
    if scope.api:
        scope_types.add(ScopeType.API)

    return [claim for claim in _claim_store.values() if scope_types.intersection(claim.scope_types)]


def _detect_conflicts(claims: list[Claim], scope: ChangeScope) -> list[Conflict]:
    conflicts: list[Conflict] = []
    by_assertion: dict[str, list[Claim]] = {}
    for claim in claims:
        key = claim.assertion.strip().lower()
        by_assertion.setdefault(key, []).append(claim)

    for assertion_key, grouped in by_assertion.items():
        if len(grouped) < 2:
            continue
        categories = {c.category for c in grouped}
        if len(categories) < 2:
            continue
        conflict_id = f"conflict-{abs(hash(assertion_key)) % (10**8)}"
        conflicts.append(
            Conflict(
                conflict_id=conflict_id,
                reason_code=ConflictReasonCode.ASSERTION_CONTRADICTION,
                question=f"Conflicting claims detected for: {grouped[0].title}",
                choices=[
                    ConflictChoice(key="approve", label="Approve", effect="Accept claim"),
                    ConflictChoice(key="reject", label="Reject", effect="Reject claim"),
                ],
                claim_ids=[c.claim_id for c in grouped],
                scope=scope,
                introduced_by="control-point",
            )
        )
    return conflicts


def gate_check(scope: ChangeScope) -> GateCheckResult:
    claims = _filter_claims(scope)
    conflicts = _detect_conflicts(claims, scope)
    blocking_claims = [c.claim_id for c in claims if c.severity == ClaimSeverity.BLOCK]
    summary = {
        "total": len(claims),
        "conflicted": len(conflicts),
        "violated": 0,
        "unknown": 0,
    }
    pass_ = not conflicts and not blocking_claims
    return GateCheckResult(
        scope=scope,
        summary=summary,
        claims=claims,
        conflicts=conflicts,
        pass_=pass_,
        blocking_claims=blocking_claims,
    )


@app.post("/claims/register", response_model=Claim)
async def register_claim_endpoint(claim: Claim) -> Claim:
    return register_claim(claim)


@app.post("/gate/check", response_model=GateCheckResult)
async def gate_check_endpoint(scope: ChangeScope) -> GateCheckResult:
    return gate_check(scope)


@app.post("/control-point/arbitrate")
async def arbitrate_endpoint(arbitration: Arbitration) -> Dict[str, Any]:
    return {"status": "accepted", "arbitration": arbitration.dict()}


@app.post("/review")
async def review(request: Request) -> JSONResponse:
    diagnostics: Dict[str, Any] = {}
    try:
        content_type = request.headers.get("content-type", "")
        plan_text = ""
        prompt_template: Optional[str] = None

        if "application/json" in content_type:
            try:
                payload = await request.json()
            except ValueError:
                diagnostics["error_source"] = "parsing"
                return JSONResponse(
                    status_code=400,
                    content={
                        "status": "error",
                        "result": "Invalid JSON body",
                        "diagnostics": diagnostics,
                    },
                )
            plan_text = str(payload.get("plan") or "").strip()
            prompt_template = payload.get("prompt_template")
        else:
            body = await request.body()
            plan_text = body.decode("utf-8").strip()

        if not plan_text:
            diagnostics["error_source"] = "parsing"
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "result": "No input provided",
                    "diagnostics": diagnostics,
                },
            )

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            diagnostics["error_source"] = "missing configuration (OPENAI_API_KEY)"
            return JSONResponse(
                status_code=500,
                content={
                    "status": "error",
                    "result": "Missing OPENAI_API_KEY",
                    "diagnostics": diagnostics,
                },
            )

        try:
            prompt = build_prompt(plan_text, prompt_template)
        except ValueError as exc:
            diagnostics["error_source"] = "parsing"
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "result": str(exc),
                    "diagnostics": diagnostics,
                },
            )
        try:
            response = requests.post(
                "https://api.openai.com/v1/responses",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "gpt-4.1-mini",
                    "input": prompt,
                },
                timeout=60,
            )
        except requests.RequestException:
            diagnostics["error_source"] = "network"
            return JSONResponse(
                status_code=502,
                content={
                    "status": "error",
                    "result": "Review failed — backend unavailable",
                    "diagnostics": diagnostics,
                },
            )

        try:
            payload = response.json()
        except ValueError:
            diagnostics["error_source"] = "parsing"
            return JSONResponse(
                status_code=502,
                content={
                    "status": "error",
                    "result": "Invalid response from API",
                    "diagnostics": diagnostics,
                },
            )

        diagnostics.update(extract_diagnostics(payload))

        if not response.ok:
            diagnostics["error_source"] = "api"
            message = payload.get("error", {}).get("message") or "API request failed"
            return JSONResponse(
                status_code=response.status_code,
                content={
                    "status": "error",
                    "result": message,
                    "diagnostics": diagnostics,
                },
            )

        try:
            result_text = extract_text(payload)
        except (KeyError, IndexError, TypeError):
            diagnostics["error_source"] = "parsing"
            return JSONResponse(
                status_code=502,
                content={
                    "status": "error",
                    "result": "Missing response text",
                    "diagnostics": diagnostics,
                },
            )

        return JSONResponse(
            status_code=200,
            content={
                "status": "ok",
                "result": result_text,
                "diagnostics": diagnostics,
            },
        )
    except Exception as exc:
        diagnostics["error_source"] = diagnostics.get("error_source") or "parsing"
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "result": str(exc),
                "diagnostics": diagnostics,
            },
        )
