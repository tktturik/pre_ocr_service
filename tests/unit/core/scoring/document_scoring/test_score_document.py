"""Тесты score_document."""

import pytest

from core.models.analysis_types import ItemResult, Verdict
from core.scoring.document_scoring import score_document


def test_score_document_verdict_and_cap(
    document_case: tuple[tuple[ItemResult, ...], Verdict],
) -> None:
    """Документ пригоден только при пригодных элементах; иначе оценка не выше 0.49."""
    items, expected = document_case

    result = score_document(items)

    assert result.suitable_for_ocr is expected.suitable_for_ocr
    assert result.quality_score == pytest.approx(expected.quality_score)
