"""Фикстуры тестов raster_scoring."""

import pytest

from core.models.analysis_types import CheckOutcome, Verdict


@pytest.fixture(
    params=[
        pytest.param(
            (
                (
                    CheckOutcome(name="check_a", passed=True, score=0.8, value=None),
                    CheckOutcome(name="check_b", passed=True, score=0.6, value=None),
                ),
                Verdict(suitable_for_ocr=True, quality_score=0.7),
            ),
            id="all_passed",
        ),
        pytest.param(
            (
                (
                    CheckOutcome(name="check_a", passed=True, score=1.0, value=None),
                    CheckOutcome(name="check_b", passed=True, score=1.0, value=None),
                    CheckOutcome(name="check_c", passed=False, score=0.4, value=None),
                ),
                Verdict(suitable_for_ocr=False, quality_score=0.49),
            ),
            id="failed_capped",
        ),
    ]
)
def raster_case(
    request: pytest.FixtureRequest,
) -> tuple[tuple[CheckOutcome, ...], Verdict]:
    """Исходы проверок элемента и ожидаемый вердикт."""
    return request.param
