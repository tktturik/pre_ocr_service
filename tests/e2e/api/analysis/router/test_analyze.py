import pytest
from fastapi.testclient import TestClient

ALL_CHECKS = "resolution,blur,contrast,illumination,noise"


@pytest.mark.parametrize(
    ("filename", "document_suitable", "items_suitable"),
    [
        ("image_009.jpg", True, [True]),
        ("image_036.png", False, [False]),
        ("image_042.png", False, [False]),
        ("document_010.pdf", False, [False, True, True]),
    ],
)
def test_analyze_returns_document_and_item_shape(
    client: TestClient,
    template_bytes: dict[str, bytes],
    filename: str,
    document_suitable: bool,
    items_suitable: list[bool],
) -> None:
    """POST /analyze на реальном файле отдаёт 200, форму ответа и булевы вердикты."""
    response = client.post(
        f"/analyze?checks={ALL_CHECKS}", content=template_bytes[filename]
    )

    body = response.json()
    assert response.status_code == 200
    assert {"suitable_for_ocr", "quality_score", "processing_time_ms", "items"} <= (
        body.keys()
    )
    assert body["items"][0]["index"] == 1
    assert {"passed", "score"} <= body["items"][0]["checks"]["blur"].keys()
    assert body["suitable_for_ocr"] is document_suitable
    assert [item["suitable_for_ocr"] for item in body["items"]] == items_suitable


def test_analyze_unknown_check_returns_400_with_details(
    client: TestClient, template_bytes: dict[str, bytes]
) -> None:
    """Неизвестная проверка даёт 400 unknown_checks и её имя в details."""
    response = client.post(
        "/analyze?checks=blur,nope", content=template_bytes["image_009.jpg"]
    )

    assert response.status_code == 400
    assert response.json()["code"] == "unknown_checks"
    assert response.json()["details"]["unknown"] == ["nope"]


def test_analyze_empty_checks_returns_400(
    client: TestClient, template_bytes: dict[str, bytes]
) -> None:
    """Пустой список проверок даёт 400 empty_checks."""
    response = client.post("/analyze?checks=", content=template_bytes["image_009.jpg"])

    assert response.status_code == 400
    assert response.json()["code"] == "empty_checks"


def test_analyze_text_body_returns_unsupported_format(
    client: TestClient, text_bytes: bytes
) -> None:
    """Текстовое тело даёт 400 unsupported_format."""
    response = client.post("/analyze?checks=blur", content=text_bytes)

    assert response.status_code == 400
    assert response.json()["code"] == "unsupported_format"
