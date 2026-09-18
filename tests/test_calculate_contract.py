from app import create_app


def test_calculate_rejects_missing_required_fields():
    client = create_app().test_client()
    response = client.post("/budgets/calculate", json={})
    assert response.status_code == 400
    assert response.get_json()["code"] == "INVALID_REQUEST"


def test_calculate_route_exists_before_engine_wiring():
    client = create_app().test_client()
    response = client.post(
        "/budgets/calculate",
        json={
            "project_id": "project-001",
            "type_system": "SICRO",
            "monetary_base_date": "2026-07",
            "services": [{
                "id": "service-001",
                "code": "SERV-001",
                "description": "Execução",
                "unit": "m²",
                "quantity": 1000,
                "compositions": [{
                    "composition_id": "composition-001",
                    "reference_base_date": "2025-07",
                    "factor": 1,
                }],
            }],
        },
    )
    assert response.status_code == 501
    assert response.get_json()["code"] == "ENGINE_NOT_CONFIGURED"
