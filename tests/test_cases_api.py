"""Unit tests for Case Management API Endpoints."""

def test_create_and_list_cases(client):
    case_payload = {
        "case_number": "CASE-2026-TEST",
        "title": "Automated Unit Test Case",
        "investigator": "Test-Runner",
        "description": "Created during pytest suite execution."
    }
    create_res = client.post("/api/v1/cases/", json=case_payload)
    assert create_res.status_code == 201
    created_data = create_res.json()
    assert created_data["case_number"] == "CASE-2026-TEST"
    assert created_data["id"] is not None

    list_res = client.get("/api/v1/cases/")
    assert list_res.status_code == 200
    cases_list = list_res.json()
    assert len(cases_list) >= 1
    assert any(c["case_number"] == "CASE-2026-TEST" for c in cases_list)
