from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


# Table-driven test cases
def test_claim_registration() -> None:
    valid_claim = {
        "claim_id": "CP-TEST-001",
        "title": "Test claim",
        "scope_types": ["repo"],
        "assertion": "test assertion",
        "severity": "block",
        "owner": "test",
        "introduced_by": "test",
        "rationale": "Test rationale.",
    }
    # Valid registration
    r = client.post("/claims/register", json=valid_claim)
    assert r.status_code == 200
    # Duplicate claim_id
    r2 = client.post("/claims/register", json=valid_claim)
    assert r2.status_code == 400
    # Missing owner
    invalid_claim = valid_claim.copy()
    invalid_claim["claim_id"] = "CP-TEST-002"
    invalid_claim["owner"] = ""
    r3 = client.post("/claims/register", json=invalid_claim)
    assert r3.status_code == 400
    # Missing scope_types
    invalid_claim2 = valid_claim.copy()
    invalid_claim2["claim_id"] = "CP-TEST-003"
    invalid_claim2["scope_types"] = []
    r4 = client.post("/claims/register", json=invalid_claim2)
    assert r4.status_code == 400


def test_scope_filtering() -> None:
    scope = {"repo": "main"}
    r = client.post("/gate/check", json=scope)
    assert r.status_code == 200
    data = r.json()
    assert "contract_version" in data
    assert "scope" in data
    assert "summary" in data
    assert "claims" in data
    assert "conflicts" in data
    # Deterministic: field order
    assert list(data.keys()) == [
        "contract_version",
        "scope",
        "summary",
        "claims",
        "conflicts",
        "pass_",
        "blocking_claims",
    ]


def test_conflict_detection() -> None:
    scope = {"repo": "main"}
    r = client.post("/gate/check", json=scope)
    data = r.json()
    # Should have at least one conflict
    assert data["conflicts"]
    for conflict in data["conflicts"]:
        assert "conflict_id" in conflict
        assert "claims_involved" in conflict
        assert "reason_code" in conflict
        assert "requires_human" in conflict


def test_arbitration() -> None:
    # Use a known conflict from previous test
    scope = {"repo": "main"}
    r = client.post("/gate/check", json=scope)
    data = r.json()
    conflict = data["conflicts"][0]
    arbitration = {
        "conflict_id": conflict["conflict_id"],
        "decision": "approve",
        "justification": "Test arbitration.",
        "scope": scope,
    }
    r2 = client.post("/control-point/arbitrate", json=arbitration)
    assert r2.status_code == 200
    result = r2.json()
    assert result["status"] == "accepted"
    assert result["arbitration"]["conflict_id"] == conflict["conflict_id"]
    assert len(result["arbitration"]["justification"]) <= 140
