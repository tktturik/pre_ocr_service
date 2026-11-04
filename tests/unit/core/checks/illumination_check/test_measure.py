from collections.abc import Callable

import numpy as np
import pytest

from core.checks.illumination_check import IlluminationCheck
from core.checks.raster_context import RasterContext
from core.models.raster_types import Raster
from core.scoring.check_scoring import make_outcome, score_value

# Множитель яркости на правом краю: сильная тень и три нарастающих уровня.
STRONG_SHADOW = 0.3
SHADOW_LEVELS = (1.0, 0.8, 0.3)


@pytest.fixture
def make_ctx() -> Callable[..., RasterContext]:
    """Фабрика контекста: светлая страница с текстом и тенью слева направо."""

    def factory(shadow: float = 1.0) -> RasterContext:
        page = np.full((400, 400), 240.0)
        for row in range(30, 370, 30):
            for col in range(20, 380, 12):
                page[row : row + 14, col : col + 6] = 30
        # Тень множит страницу: слева 1.0, справа shadow.
        page *= np.linspace(1.0, shadow, 400)[None, :]
        pixels = np.clip(page, 0, 255).astype(np.uint8)
        return RasterContext(Raster(index=0, pixels=pixels))

    return factory


@pytest.mark.parametrize(
    ("shadow", "expected_passed"),
    [(1.0, True), (STRONG_SHADOW, False)],
)
def test_measure_uniform_passes_strong_shadow_fails(
    make_ctx: Callable[..., RasterContext],
    shadow: float,
    expected_passed: bool,
) -> None:
    """Равномерный фон проходит проверку, сильная тень её проваливает."""
    check = IlluminationCheck()

    value = check.measure(make_ctx(shadow=shadow))
    outcome = make_outcome(check.name, value, check.points)

    assert outcome.passed is expected_passed


def test_measure_score_falls_as_shadow_grows(
    make_ctx: Callable[..., RasterContext],
) -> None:
    """Скор illumination падает с ростом силы тени."""
    check = IlluminationCheck()

    values = [check.measure(make_ctx(shadow=s)) for s in SHADOW_LEVELS]
    assert None not in values
    scores = [score_value(v, check.points) for v in values if v is not None]

    assert scores[0] > scores[2]
    assert scores[0] >= scores[1] >= scores[2]
