from fastapi import FastAPI, HTTPException
from typing import List

from .models import (
    Claim,
    ClaimSeverity,
    ChangeScope,
    Conflict,
    ConflictChoice,
    ScopeType,
    ConflictReasonCode,
    Arbitration,
    Vocabulary,
    GateResult,
)


app = FastAPI()

# Import and register the claim importer router
try:
    from .importer import importer_router

    app.include_router(importer_router)
except ImportError:
    pass

# Hardcoded sample claims (in-memory, deterministic)
claims: List[Claim] = [
    Claim(
        claim_id="CP-ENV-001",
        title="Environment is first-class",
        scope_types=[ScopeType.REPO, ScopeType.SUBSYSTEM],
        assertion="environment is first-class",
        severity=ClaimSeverity.BLOCK,
        owner="env",
        introduced_by="invariant",
        rationale="All environments must be explicit and first-class.",
        category=Vocabulary.INVARIANT,
    ),
    # Roundhouse: Explicit Arbitration Required
    Claim(
        claim_id="RH-ARBITRATION-001",
        title="Explicit Arbitration Required",
        scope_types=[ScopeType.REPO, ScopeType.SUBSYSTEM, ScopeType.API],
        assertion="Conflicting claims require explicit arbitration",
        severity=ClaimSeverity.BLOCK,
        owner="control-point",
        introduced_by="prohibition",
        rationale="No silent overrides; all conflicts must be resolved.",
        category=Vocabulary.PROHIBITION,
    ),
    # Control Point: Gate Enforcement
    Claim(
        claim_id="CP-GATE-001",
        title="Gate Enforcement",
        scope_types=[ScopeType.REPO, ScopeType.SUBSYSTEM, ScopeType.API],
        assertion="All changes must pass through Control Point",
        severity=ClaimSeverity.BLOCK,
        owner="control-point",
        introduced_by="invariant",
        rationale="Ensures a single, unavoidable gate for all changes.",
        category=Vocabulary.INVARIANT,
    ),
    # Control Point: Machine-Readable Contracts
    Claim(
        claim_id="CP-CONTRACT-001",
        title="Machine-Readable Contracts",
        scope_types=[ScopeType.REPO],
        assertion="All contracts must be machine-readable and versioned",
        severity=ClaimSeverity.BLOCK,
        owner="control-point",
        introduced_by="requirement",
        rationale="Prevents document drift and ambiguity.",
        category=Vocabulary.REQUIREMENT,
    ),
    # Control Point: No Document-Based Authority
    Claim(
        claim_id="CP-NODOC-001",
        title="No Document-Based Authority",
        scope_types=[ScopeType.REPO],
        assertion="No document is authoritative; only claims are",
        severity=ClaimSeverity.BLOCK,
        owner="control-point",
        introduced_by="prohibition",
        rationale="Eliminates prose-based authority and sprawl.",
        category=Vocabulary.PROHIBITION,
    ),
    # Control Point: Conflict Framing
    Claim(
        claim_id="CP-CONFLICT-001",
        title="Conflict Framing",
        scope_types=[ScopeType.REPO, ScopeType.SUBSYSTEM, ScopeType.API],
        assertion="All conflicts must be framed as explicit questions with choices",
        severity=ClaimSeverity.BLOCK,
        owner="control-point",
        introduced_by="constraint",
        rationale="Ensures actionable, deterministic arbitration.",
        category=Vocabulary.CONSTRAINT,
    ),
    Claim(
        claim_id="CP-API-001",
        title="APIs must be environment-scoped",
        scope_types=[ScopeType.API, ScopeType.REPO],
        assertion="all APIs must be environment-scoped",
        severity=ClaimSeverity.BLOCK,
        owner="api",
        introduced_by="constraint",
        rationale="APIs must not have global side effects.",
        category=Vocabulary.CONSTRAINT,
    ),
    Claim(
        claim_id="CP-UI-001",
        title="UI must not compute readiness locally",
        scope_types=[ScopeType.SUBSYSTEM],
        assertion="UI must not compute readiness locally",
        severity=ClaimSeverity.WARN,
        owner="ui",
        introduced_by="rule",
        rationale="Readiness must be computed by backend, not UI.",
        category=Vocabulary.REQUIREMENT,
    ),
    Claim(
        claim_id="CP-ENV-002",
        title="Snapshots must never be treated as authoritative",
        scope_types=[ScopeType.REPO, ScopeType.SUBSYSTEM],
        assertion="snapshots must never be treated as authoritative",
        severity=ClaimSeverity.BLOCK,
        owner="env",
        introduced_by="invariant",
        rationale="Snapshots are for diagnostics, not source of truth.",
        category=Vocabulary.INVARIANT,
    ),
    # Example conflicting claim
    Claim(
        claim_id="CP-ENV-003",
        title="Snapshots may be treated as authoritative",
        scope_types=[ScopeType.REPO, ScopeType.SUBSYSTEM],
        assertion="snapshots may be treated as authoritative",
        severity=ClaimSeverity.BLOCK,
        owner="env",
        introduced_by="invariant",
        rationale="Some subsystems may allow authoritative snapshots.",
        category=Vocabulary.INVARIANT,
    ),
]


def claims_for_scope(scope: ChangeScope) -> List[Claim]:
    # For demo: match if any scope_types matches a scope value
    scope_keys = set()
    if scope.repo:
        scope_keys.add(ScopeType.REPO)
    if scope.path:
        scope_keys.add(ScopeType.PATH)
    if scope.subsystem:
        scope_keys.add(ScopeType.SUBSYSTEM)
    if scope.api:
        scope_keys.add(ScopeType.API)
    return [c for c in claims if any(st in scope_keys for st in c.scope_types)]


def conflict_index(affected_claims: List[Claim]) -> List[Conflict]:
    # Deterministic conflict detection and IDs, with question framing
    conflicts = []
    seen = set()
    for i, c1 in enumerate(affected_claims):
        for j, c2 in enumerate(affected_claims):
            if i >= j:
                continue
            # Example: conflicting if assertions are negations (very naive)
            if (
                c1.assertion.replace("never", "may") == c2.assertion
                or c2.assertion.replace("never", "may") == c1.assertion
            ):
                ids = sorted([c1.claim_id, c2.claim_id])
                conflict_id = f"conflict-{'-'.join(ids)}"
                if conflict_id not in seen:
                    seen.add(conflict_id)
                    question = f"Allow {c2.assertion}?"
                    choices = [
                        ConflictChoice(
                            key="reject",
                            label="Reject change",
                            effect="Change is blocked",
                        ),
                        ConflictChoice(
                            key="allow_once",
                            label="Allow for this scope only",
                            effect="Change proceeds for this scope",
                        ),
                    ]
                    # Use a minimal ChangeScope for the conflict
                    scope = ChangeScope()
                    if c1.scope_types:
                        # Assign the first scope type as a hint (not perfect, but deterministic)
                        if ScopeType.REPO in c1.scope_types:
                            scope.repo = "*"
                        if ScopeType.PATH in c1.scope_types:
                            scope.path = "*"
                        if ScopeType.SUBSYSTEM in c1.scope_types:
                            scope.subsystem = "*"
                        if ScopeType.API in c1.scope_types:
                            scope.api = "*"
                    conflicts.append(
                        Conflict(
                            conflict_id=conflict_id,
                            reason_code=ConflictReasonCode.ASSERTION_CONTRADICTION,
                            question=question,
                            choices=choices,
                            claim_ids=ids,
                            scope=scope,
                            introduced_by=c1.introduced_by,
                        )
                    )
    return conflicts


@app.get("/claims", response_model=List[Claim])
def list_claims():
    return claims


@app.post("/claims/register", response_model=Claim)
def register_claim(claim: Claim):
    # Registration gate: schema validation, uniqueness, owner, scope compatibility
    if any(c.claim_id == claim.claim_id for c in claims):
        raise HTTPException(status_code=400, detail="claim_id must be unique")
    if not claim.owner:
        raise HTTPException(status_code=400, detail="owner must be present")
    if not claim.scope_types:
        raise HTTPException(status_code=400, detail="scope_types must not be empty")
    claims.append(claim)
    return claim


@app.get("/claims/{claim_id}", response_model=Claim)
def get_claim(claim_id: str):
    for claim in claims:
        if claim.claim_id == claim_id:
            return claim
    raise HTTPException(status_code=404, detail="Claim not found")


@app.post("/evaluate", response_model=List[Claim])
def evaluate_claims():
    # In-memory, deterministic: just return current states
    return claims


@app.post("/gate/check", response_model=GateResult)
def gate_check(scope: ChangeScope):
    affected = claims_for_scope(scope)
    conflicts = conflict_index(affected)
    blocking = [c.claim_id for c in affected]  # For demo, all are blocking if present
    summary = {
        "affected": len(affected),
        "violated": 0,  # Not implemented in this stub
        "conflicted": len(conflicts),
        "unknown": 0,  # Not implemented in this stub
    }
    return GateResult(
        contract_version=1,
        scope=scope,
        summary=summary,
        claims=affected,
        conflicts=conflicts,
        pass_=(len(blocking) == 0 and not conflicts),
        blocking_claims=blocking,
    )


@app.post("/control-point/arbitrate", response_model=dict)
def arbitrate(arbitration: Arbitration):
    # Accept only valid choice keys (for demo: 'reject', 'allow_once')
    if arbitration.decision not in ["reject", "allow_once"]:
        return {"status": "rejected", "reason": "Invalid choice key"}
    return {"status": "accepted", "arbitration": arbitration.dict()}
