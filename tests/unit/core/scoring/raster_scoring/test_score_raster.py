"""Тесты score_raster."""

import pytest

from core.models.analysis_types import CheckOutcome, Verdict
from core.scoring.raster_scoring import score_raster


def test_score_raster_verdict_and_cap(
    raster_case: tuple[tuple[CheckOutcome, ...], Verdict],
) -> None:
    """Элемент пригоден только при всех пройденных; при провале оценка не выше 0.49."""
    outcomes, expected = raster_case

    result = score_raster(outcomes)

    assert result.suitable_for_ocr is expected.suitable_for_ocr
    assert result.quality_score == pytest.approx(expected.quality_score)
