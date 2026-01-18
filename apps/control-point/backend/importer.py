import re
import json
from fastapi import APIRouter, UploadFile, File, HTTPException
from .models import Claim, ChangeScope
from typing import List

importer_router = APIRouter()


def classify_sentence(sentence: str) -> str:
    sentence = sentence.lower()
    if re.search(r"must not|is not allowed|never", sentence):
        return "prohibition"
    if re.search(r"must|only if|is responsible for|required", sentence):
        return "requirement"
    if re.search(r"always|never changes|authoritative", sentence):
        return "invariant"
    if re.search(r"does|is|exists", sentence):
        return "capability"
    if re.search(r"why|goal|purpose", sentence):
        return "constraint"
    if re.search(r"first|then|after", sentence):
        return "constraint"
    return "constraint"


def normalize_assertion(sentence: str) -> str:
    # Minimal normalization: strip, collapse spaces
    return re.sub(r"\s+", " ", sentence.strip())


def infer_scope_types(sentence: str) -> List[str]:
    scopes = []
    s = sentence.lower()
    if re.search(r"api|endpoint", s):
        scopes.append("api")
    if re.search(r"ui|frontend", s):
        scopes.append("subsystem")
    if re.search(r"backend|service", s):
        scopes.append("subsystem")
    if re.search(r"repo-wide|system", s):
        scopes.append("repo")
    if re.search(r"device|panel", s):
        scopes.append("subsystem")
    return scopes or ["repo"]


def infer_severity(sentence: str) -> str:
    s = sentence.lower()
    if re.search(r"must not|never", s):
        return "block"
    if re.search(r"must|required", s):
        return "block"
    if re.search(r"should|recommended", s):
        return "warn"
    return "warn"


def infer_owner(sentence: str) -> str:
    s = sentence.lower()
    for owner in ["ui", "env", "control-point", "api", "subsystem", "repo", "node"]:
        if owner in s:
            return owner
    return "unassigned"


def extract_sentences(text: str) -> List[str]:
    # Split on periods, bullets, headings
    sentences = re.split(r"[\n\r\-\*]+|\. ?", text)
    return [s.strip() for s in sentences if s.strip()]


@importer_router.post("/claims/import", response_model=List[Claim])
async def import_claims(file: UploadFile = File(...)):
    """
    Import claims from a text or JSON file, distill into atomic claims, run each through the registration gate, and mark as imported.
    Stops and emits conflicts if any arise.
    """
    try:
        content = await file.read()
        # Accept either JSON (list of sentences) or raw text
        try:
            data = json.loads(content)
            if isinstance(data, list):
                sentences = [str(s) for s in data]
            elif isinstance(data, str):
                sentences = extract_sentences(data)
            else:
                raise ValueError
        except Exception:
            # Fallback: treat as raw text
            sentences = extract_sentences(content.decode("utf-8"))

        candidate_claims = []
        for sentence in sentences:
            kind = classify_sentence(sentence)
            if kind not in ("requirement", "prohibition", "invariant", "constraint", "capability"):
                continue
            assertion = normalize_assertion(sentence)
            scope_types = infer_scope_types(sentence)
            severity = infer_severity(sentence)
            owner = infer_owner(sentence)
            claim = Claim(
                claim_id=f"imported-{abs(hash(assertion)) % (10**8)}",
                title=assertion[:60],
                scope_types=scope_types,
                assertion=assertion,
                severity=severity,
                owner=owner,
                introduced_by=file.filename or "imported",
                rationale="Imported from document",
                category=kind,
                source_type="imported",
            )
            candidate_claims.append(claim)

        # Import here to avoid circular import during app startup.
        from . import main as backend_main

        imported = []
        for claim in candidate_claims:
            # Gate registration: schema, uniqueness, conflict
            try:
                imported_claim = backend_main.register_claim(claim)
                imported.append(imported_claim)
            except HTTPException as e:
                # If uniqueness fails, skip
                if e.status_code == 400 and "unique" in str(e.detail):
                    continue
                raise

        # Run gate check for all imported claims
        scope = ChangeScope()
        if imported:
            # Use the first imported claim's scope_types as a hint
            st = imported[0].scope_types
            if "repo" in st:
                scope.repo = "*"
            if "subsystem" in st:
                scope.subsystem = "*"
            if "api" in st:
                scope.api = "*"
            if "ui" in st:
                scope.subsystem = "ui"
            if "node" in st:
                scope.subsystem = "node"
            gate_result = backend_main.gate_check(scope)
            if hasattr(gate_result, "conflicts") and gate_result.conflicts:
                raise HTTPException(
                    status_code=409,
                    detail={"conflicts": [c.dict() for c in gate_result.conflicts]},
                )
        return imported
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Import failed: {str(e)}")
