from fastapi.testclient import TestClient


def test_get_checks_returns_registered_names(client: TestClient) -> None:
    """GET /checks отдаёт 200 и список с зарегистрированной проверкой constant."""
    response = client.get("/checks")

    assert response.status_code == 200
    assert "constant" in response.json()["checks"]
