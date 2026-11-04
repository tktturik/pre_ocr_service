import numpy as np

from core.models.analysis_types import CheckOutcome, ScorePoints

# Скор 0.5 - passed; проверка считается пройденной с этого значения.
_PASS_SCORE = 0.5


def score_value(value: float, points: ScorePoints) -> float:
    """Переводит сырое значение проверки в скор 0..1 по опорным точкам.

    Между точками линейная интерполяция, за пределами диапазона скор обрезается.
    Порядок bad и good может быть любым: точки сортируются по значению.
    """
    xs = (points.bad, points.passed, points.good)
    ys = (0.0, _PASS_SCORE, 1.0)
    if xs[0] > xs[2]:
        xs, ys = xs[::-1], ys[::-1]
    return float(np.interp(value, xs, ys))


def make_outcome(name: str, value: float | None, points: ScorePoints) -> CheckOutcome:
    """Строит исход проверки.

    Значение `None` (проверку не удалось измерить) считается провалом:
    passed=False, score=0.0, value=None. Иначе скор считается по точкам.
    """
    if value is None:
        return CheckOutcome(name=name, passed=False, score=0.0, value=None)
    score = score_value(value, points)
    return CheckOutcome(
        name=name, passed=score >= _PASS_SCORE, score=score, value=value
    )
