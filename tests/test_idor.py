"""Security Tests for Insecure Direct Object Reference (IDOR) Prevention."""

from conftest import get_auth_token


def test_idor_case_access_blocked_for_unauthorized_user(client, investigator_headers):
    # 1. Investigator 1 creates a private case
    case_res = client.post(
        "/api/v1/cases/",
        json={"case_number": "CASE-IDOR-888", "title": "Confidential Investigation"},
        headers=investigator_headers,
    )
    assert case_res.status_code == 201
    case_id = case_res.json()["id"]

    # 2. Attach an evidence item
    ev_res = client.post(
        f"/api/v1/cases/{case_id}/evidence",
        json={
            "item_number": "EVID-SECRET-01",
            "title": "Secret Drive Dump",
            "file_path": "/evidence/secret.raw",
        },
        headers=investigator_headers,
    )
    assert ev_res.status_code == 201
    evidence_id = ev_res.json()["id"]

    # 3. Create a second investigator headers (unauthorized for Case IDOR-888)
    # Register/login second user or use viewer
    viewer_token = get_auth_token(client, "viewer1", "ViewerPass123!")
    viewer_headers = {"Authorization": f"Bearer {viewer_token}"}

    # 4. Attempt to access Case details -> Should be BLOCKED with IDOR_ACCESS_DENIED
    res_case = client.get(f"/api/v1/cases/{case_id}", headers=viewer_headers)
    assert res_case.status_code == 403
    assert res_case.json()["error"]["code"] == "IDOR_ACCESS_DENIED"

    # 5. Attempt to view Evidence Item -> Should be BLOCKED with IDOR_ACCESS_DENIED
    res_ev = client.get(f"/api/v1/evidence/{evidence_id}", headers=viewer_headers)
    assert res_ev.status_code == 403
    assert res_ev.json()["error"]["code"] == "IDOR_ACCESS_DENIED"


def test_idor_case_access_allowed_after_explicit_grant(client, investigator_headers, admin_headers):
    # 1. Investigator 1 creates a case
    case_res = client.post(
        "/api/v1/cases/",
        json={"case_number": "CASE-GRANT-999", "title": "Shared Investigation"},
        headers=investigator_headers,
    )
    case_id = case_res.json()["id"]

    operator_token = get_auth_token(client, "operator1", "OperatorPass123!")
    operator_headers = {"Authorization": f"Bearer {operator_token}"}

    # 2. Operator initially blocked
    res_before = client.get(f"/api/v1/cases/{case_id}", headers=operator_headers)
    assert res_before.status_code == 403

    # 3. Investigator 1 grants access to Operator 1 (user_id=3)
    grant_res = client.post(
        f"/api/v1/cases/{case_id}/grant-access",
        json={"user_id": 3},
        headers=investigator_headers,
    )
    assert grant_res.status_code == 200

    # 4. Operator can now access Case details successfully
    res_after = client.get(f"/api/v1/cases/{case_id}", headers=operator_headers)
    assert res_after.status_code == 200
    assert res_after.json()["case_number"] == "CASE-GRANT-999"
