from fastapi.testclient import TestClient


def test_analyze_returns_document_and_item_shape(
    client: TestClient, png_bytes: bytes
) -> None:
    """POST /analyze с PNG отдаёт 200 и форму ответа с исходом проверки."""
    response = client.post("/analyze?checks=constant", content=png_bytes)

    body = response.json()
    assert response.status_code == 200
    assert {"suitable_for_ocr", "quality_score", "processing_time_ms", "items"} <= (
        body.keys()
    )
    assert body["items"][0]["index"] == 1
    assert {"passed", "score"} <= body["items"][0]["checks"]["constant"].keys()


def test_analyze_unknown_check_returns_400_with_details(
    client: TestClient, png_bytes: bytes
) -> None:
    """Неизвестная проверка даёт 400 unknown_checks и её имя в details."""
    response = client.post("/analyze?checks=constant,nope", content=png_bytes)

    assert response.status_code == 400
    assert response.json()["code"] == "unknown_checks"
    assert response.json()["details"]["unknown"] == ["nope"]


def test_analyze_empty_checks_returns_400(
    client: TestClient, png_bytes: bytes
) -> None:
    """Пустой список проверок даёт 400 empty_checks."""
    response = client.post("/analyze?checks=", content=png_bytes)

    assert response.status_code == 400
    assert response.json()["code"] == "empty_checks"


def test_analyze_text_body_returns_unsupported_format(
    client: TestClient, text_bytes: bytes
) -> None:
    """Текстовое тело даёт 400 unsupported_format."""
    response = client.post("/analyze?checks=constant", content=text_bytes)

    assert response.status_code == 400
    assert response.json()["code"] == "unsupported_format"
