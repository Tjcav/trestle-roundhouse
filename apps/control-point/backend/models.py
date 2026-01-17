from __future__ import annotations
from enum import Enum
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, validator


class ClaimSeverity(str, Enum):
    BLOCK = "block"
    WARN = "warn"


class ScopeType(str, Enum):
    REPO = "repo"
    PATH = "path"
    SUBSYSTEM = "subsystem"
    API = "api"


class ChangeScope(BaseModel):
    repo: Optional[str] = None
    path: Optional[str] = None
    subsystem: Optional[str] = None
    api: Optional[str] = None


class Vocabulary(str, Enum):
    REQUIREMENT = "requirement"
    INVARIANT = "invariant"
    CONSTRAINT = "constraint"
    CAPABILITY = "capability"
    PROHIBITION = "prohibition"


class Claim(BaseModel):
    claim_id: str
    title: str
    scope_types: List[ScopeType]
    assertion: str
    severity: ClaimSeverity
    owner: str
    introduced_by: str
    rationale: str = Field(..., max_length=140)
    category: Vocabulary
    read_only: bool = False
    source_type: Optional[str] = None
    rationale_ref: Optional[str] = None

    @validator("claim_id")
    def id_must_be_stable(cls, v):
        if not v or not v.strip():
            raise ValueError("claim_id must be non-empty")
        return v

    @validator("owner")
    def owner_must_be_present(cls, v):
        if not v or not v.strip():
            raise ValueError("owner must be present")
        return v

    @validator("scope_types")
    def scope_types_must_not_be_empty(cls, v):
        if not v:
            raise ValueError("scope_types must not be empty")
        return v

    @validator("category")
    def category_must_be_closed(cls, v):
        if v not in Vocabulary.__members__.values():
            raise ValueError("category must be a closed vocabulary")
        return v


class ClaimState(str, Enum):
    SATISFIED = "satisfied"
    VIOLATED = "violated"
    UNKNOWN = "unknown"
    CONFLICTED = "conflicted"


class ConflictReasonCode(str, Enum):
    SCOPE_OVERLAP = "scope_overlap"
    ASSERTION_CONTRADICTION = "assertion_contradiction"
    OWNER_DISAGREEMENT = "owner_disagreement"


class ConflictChoice(BaseModel):
    key: str
    label: str
    effect: str


class Conflict(BaseModel):
    conflict_id: str
    reason_code: ConflictReasonCode
    question: str
    choices: List[ConflictChoice]
    claim_ids: List[str]
    scope: ChangeScope
    introduced_by: str


# Aggregate gate result model
class GateResult(BaseModel):
    contract_version: Literal[1] = 1
    scope: ChangeScope
    summary: dict
    claims: List[Claim]
    conflicts: List[Conflict]
    pass_: bool
    blocking_claims: List[str]


class ArbitrationDecision(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"
    REVISE = "revise"


class Arbitration(BaseModel):
    conflict_id: str
    decision: ArbitrationDecision
    justification: str = Field(..., max_length=140)
    scope: ChangeScope


# GateCheckResult model for gate/check endpoint
class GateCheckResult(BaseModel):
    contract_version: Literal[1] = 1
    scope: ChangeScope
    summary: dict
    claims: List[Claim]
    conflicts: List["Conflict"]
    pass_: bool
    blocking_claims: List[str]

    class Config:
        extra = "forbid"
        fields = {
            "contract_version": {"order": 0},
            "scope": {"order": 1},
            "summary": {"order": 2},
            "claims": {"order": 3},
            "conflicts": {"order": 4},
            "pass_": {"order": 5},
            "blocking_claims": {"order": 6},
        }
