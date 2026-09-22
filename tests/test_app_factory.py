from fastapi.testclient import TestClient

from app import create_app


def test_create_app():
    app = create_app()

    assert app is not None
    assert app.title == "Budget Engine"


def test_health_route_is_registered():
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}