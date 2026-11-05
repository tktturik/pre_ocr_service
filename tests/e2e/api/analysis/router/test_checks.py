from fastapi.testclient import TestClient


def test_get_checks_returns_registered_names(client: TestClient) -> None:
    """GET /checks отдаёт 200 и проверки по умолчанию в порядке регистрации."""
    response = client.get("/checks")

    assert response.status_code == 200
    assert response.json()["checks"] == [
        "resolution",
        "blur",
        "contrast",
        "illumination",
        "noise",
        "skew",
    ]
