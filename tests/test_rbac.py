"""Security Tests for Role-Based Access Control (RBAC) & Privilege Escalation Prevention."""

def test_viewer_cannot_create_case(client, viewer_headers):
    payload = {
        "case_number": "CASE-ESCALATION-001",
        "title": "Unauthorized Case Creation",
        "description": "Viewer attempting to create case."
    }
    res = client.post("/api/v1/cases/", json=payload, headers=viewer_headers)
    assert res.status_code == 403
    data = res.json()
    assert data["error"]["code"] == "PERMISSION_DENIED"
    assert "Viewer" in data["error"]["message"]


def test_viewer_cannot_start_sanitization_job(client, viewer_headers):
    payload = {
        "case_id": 1,
        "reason": "Viewer attempting unauthorized sanitization job.",
        "target_identifier": "/dev/sda1",
        "explicit_confirmation": "CONFIRM_SENSITIVE_ACTION",
        "simulate": True
    }
    res = client.post("/api/v1/jobs/sanitization", json=payload, headers=viewer_headers)
    assert res.status_code == 403
    data = res.json()
    assert data["error"]["code"] == "PERMISSION_DENIED"


def test_operator_cannot_create_case(client, operator_headers):
    payload = {
        "case_number": "CASE-OPERATOR-001",
        "title": "Operator Case Creation Test"
    }
    res = client.post("/api/v1/cases/", json=payload, headers=operator_headers)
    assert res.status_code == 403
    data = res.json()
    assert data["error"]["code"] == "PERMISSION_DENIED"


def test_investigator_can_create_case(client, investigator_headers):
    payload = {
        "case_number": "CASE-INV-101",
        "title": "Authorized Investigator Case",
        "description": "Created by investigator1"
    }
    res = client.post("/api/v1/cases/", json=payload, headers=investigator_headers)
    assert res.status_code == 201
    data = res.json()
    assert data["case_number"] == "CASE-INV-101"
