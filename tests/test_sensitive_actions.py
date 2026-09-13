"""Security Tests for Sensitive Action Confirmation Guards."""

def test_sensitive_job_invalid_confirmation_rejection(client, operator_headers, investigator_headers):
    # Create case
    case_res = client.post(
        "/api/v1/cases/",
        json={"case_number": "CASE-SENSITIVE-01", "title": "Sensitive Action Case"},
        headers=investigator_headers,
    )
    case_id = case_res.json()["id"]

    # Grant access to operator
    client.post(f"/api/v1/cases/{case_id}/grant-access", json={"user_id": 3}, headers=investigator_headers)

    # 1. Attempt sanitization with missing / invalid confirmation string
    payload_wrong_conf = {
        "case_id": case_id,
        "reason": "Routine drive wipe after forensic extraction",
        "target_identifier": "/dev/sdb1",
        "explicit_confirmation": "YES",
        "simulate": True,
    }
    res = client.post("/api/v1/jobs/sanitization", json=payload_wrong_conf, headers=operator_headers)
    assert res.status_code == 400
    data = res.json()
    assert data["error"]["code"] == "INVALID_CONFIRMATION"
    assert "explicit_confirmation='CONFIRM_SENSITIVE_ACTION'" in data["error"]["message"]


def test_sensitive_job_short_reason_rejection(client, operator_headers, investigator_headers):
    # Create case
    case_res = client.post(
        "/api/v1/cases/",
        json={"case_number": "CASE-SENSITIVE-02", "title": "Sensitive Action Reason Test"},
        headers=investigator_headers,
    )
    case_id = case_res.json()["id"]

    client.post(f"/api/v1/cases/{case_id}/grant-access", json={"user_id": 3}, headers=investigator_headers)

    # Attempt with short reason
    payload_short_reason = {
        "case_id": case_id,
        "reason": "wipe",  # < 5 chars
        "target_identifier": "/dev/sdb1",
        "explicit_confirmation": "CONFIRM_SENSITIVE_ACTION",
        "simulate": True,
    }
    res = client.post("/api/v1/jobs/sanitization", json=payload_short_reason, headers=operator_headers)
    assert res.status_code == 400
    data = res.json()
    assert data["error"]["code"] == "INVALID_REASON"


def test_sensitive_job_valid_execution(client, operator_headers, investigator_headers):
    # Create case
    case_res = client.post(
        "/api/v1/cases/",
        json={"case_number": "CASE-SENSITIVE-03", "title": "Valid Execution Case"},
        headers=investigator_headers,
    )
    case_id = case_res.json()["id"]

    client.post(f"/api/v1/cases/{case_id}/grant-access", json={"user_id": 3}, headers=investigator_headers)

    payload_valid = {
        "case_id": case_id,
        "reason": "Authorized forensic partition sanitization dry-run",
        "target_identifier": "/dev/sdb1",
        "explicit_confirmation": "CONFIRM_SENSITIVE_ACTION",
        "simulate": True,
    }
    res = client.post("/api/v1/jobs/sanitization", json=payload_valid, headers=operator_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "SIMULATED"
    assert data["job_type"] == "SANITIZATION"
