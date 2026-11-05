"""Тесты make_outcome."""

from core.models.analysis_types import ScorePoints
from core.scoring.check_scoring import make_outcome


def test_make_outcome_none_value_fails_with_zero_score(
    check_name: str, score_points: ScorePoints
) -> None:
    """Значение None даёт passed False, score 0.0 и value None."""
    outcome = make_outcome(check_name, None, score_points)

    assert outcome.passed is False
    assert outcome.score == 0.0
    assert outcome.value is None
