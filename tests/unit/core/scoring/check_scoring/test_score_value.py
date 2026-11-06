"""Тесты score_value."""

import pytest

from core.models.analysis_types import ScorePoints
from core.scoring.check_scoring import score_value


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (-1.0, 0.0),
        (0.0, 0.0),
        (2.5, 0.25),
        (5.0, 0.5),
        (7.5, 0.75),
        (10.0, 1.0),
        (11.0, 1.0),
    ],
)
def test_score_value_ascending_scale(
    value: float, expected: float, score_points: ScorePoints
) -> None:
    """Прямая шкала (bad < good) линейно растёт от 0 до 1 и обрезается по краям."""
    result = score_value(value, score_points)

    assert result == pytest.approx(expected)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (11.0, 0.0),
        (10.0, 0.0),
        (7.5, 0.25),
        (5.0, 0.5),
        (2.5, 0.75),
        (0.0, 1.0),
        (-1.0, 1.0),
    ],
)
def test_score_value_descending_scale(
    value: float, expected: float, reverse_score_points: ScorePoints
) -> None:
    """Обратная шкала (bad > good) линейно убывает от 0 до 1 и обрезается по краям."""
    result = score_value(value, reverse_score_points)

    assert result == pytest.approx(expected)
