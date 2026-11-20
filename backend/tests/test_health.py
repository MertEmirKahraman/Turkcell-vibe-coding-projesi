from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_health_endpoint_returns_standard_response() -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "data": {"status": "ok"},
        "error": None,
    }


def test_unknown_route_returns_standard_error_response() -> None:
    response = client.get("/api/v1/unknown")

    assert response.status_code == 404
    assert response.json() == {
        "success": False,
        "data": None,
        "error": {
            "code": "http_404",
            "message": "Not Found",
            "details": None,
        },
    }