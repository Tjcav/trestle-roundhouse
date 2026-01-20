import json
import re

from fastapi import APIRouter, File, HTTPException, UploadFile

from .models import ChangeScope, Claim, ClaimSeverity, ScopeType, Vocabulary

importer_router = APIRouter()


def classify_sentence(sentence: str) -> Vocabulary | None:
    sentence = sentence.lower()
    if re.search(r"must not|is not allowed|never", sentence):
        return Vocabulary.PROHIBITION
    if re.search(r"must|only if|is responsible for|required", sentence):
        return Vocabulary.REQUIREMENT
    if re.search(r"always|never changes|authoritative", sentence):
        return Vocabulary.INVARIANT
    if re.search(r"does|is|exists", sentence):
        return Vocabulary.CAPABILITY
    if re.search(r"why|goal|purpose", sentence):
        return Vocabulary.CONSTRAINT
    if re.search(r"first|then|after", sentence):
        return Vocabulary.CONSTRAINT
    return Vocabulary.CONSTRAINT


def normalize_assertion(sentence: str) -> str:
    # Minimal normalization: strip, collapse spaces
    return re.sub(r"\s+", " ", sentence.strip())


def infer_scope_types(sentence: str) -> list[ScopeType]:
    scopes: list[ScopeType] = []
    s = sentence.lower()
    if re.search(r"api|endpoint", s):
        scopes.append(ScopeType.API)
    if re.search(r"ui|frontend", s):
        scopes.append(ScopeType.SUBSYSTEM)
    if re.search(r"backend|service", s):
        scopes.append(ScopeType.SUBSYSTEM)
    if re.search(r"repo-wide|system", s):
        scopes.append(ScopeType.REPO)
    if re.search(r"device|panel", s):
        scopes.append(ScopeType.SUBSYSTEM)
    return scopes or [ScopeType.REPO]


def infer_severity(sentence: str) -> ClaimSeverity:
    s = sentence.lower()
    if re.search(r"must not|never", s):
        return ClaimSeverity.BLOCK
    if re.search(r"must|required", s):
        return ClaimSeverity.BLOCK
    if re.search(r"should|recommended", s):
        return ClaimSeverity.WARN
    return ClaimSeverity.WARN


def infer_owner(sentence: str) -> str:
    s = sentence.lower()
    for owner in ["ui", "env", "control-point", "api", "subsystem", "repo", "node"]:
        if owner in s:
            return owner
    return "unassigned"


def extract_sentences(text: str) -> list[str]:
    # Split on periods, bullets, headings
    sentences = re.split(r"[\n\r\-\*]+|\. ?", text)
    return [s.strip() for s in sentences if s.strip()]


@importer_router.post("/claims/import", response_model=list[Claim])
async def import_claims(file: UploadFile = File(...)) -> list[Claim]:
    """
    Import claims from a text or JSON file, distill into atomic claims,
    run each through the registration gate, and mark as imported.
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
            if kind is None:
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
            first_claim = imported[0]
            st = first_claim.scope_types
            if ScopeType.REPO in st:
                scope.repo = "*"
            if ScopeType.SUBSYSTEM in st:
                scope.subsystem = "*"
            if ScopeType.API in st:
                scope.api = "*"
            if ScopeType.SUBSYSTEM in st and "ui" in first_claim.assertion.lower():
                scope.subsystem = "ui"
            if ScopeType.SUBSYSTEM in st and "node" in first_claim.assertion.lower():
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
