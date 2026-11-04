from collections.abc import Callable

import numpy as np
import pytest

from core.checks.raster_context import RasterContext
from core.checks.tonal_range_check import TonalRangeCheck
from core.models.raster_types import Raster

# Допуск сценария 2: сдвиг значения от тени (по абсолютной величине).
# Меньше расстояния между точками шкалы 0.15 / 0.3 / 0.5, чтобы тень
# не меняла вердикт; выбран по верхней оценке, уточнить по замерам.
SHADOW_TOLERANCE = 0.1


@pytest.fixture
def make_ctx() -> Callable[..., RasterContext]:
    """Фабрика контекста: белая страница с рядами тёмных штрихов и тенью."""

    def factory(ink: int, shadow: float = 1.0) -> RasterContext:
        page = np.full((400, 400), 255.0)
        for row in range(30, 370, 30):
            for col in range(20, 380, 12):
                page[row : row + 14, col : col + 6] = ink
        # Тень множит всю страницу (фон и чернила): слева 1.0, справа shadow.
        page *= np.linspace(1.0, shadow, 400)[None, :]
        pixels = np.clip(page, 0, 255).astype(np.uint8)
        return RasterContext(Raster(index=0, pixels=pixels))

    return factory


def test_measure_faded_text_lowers_value(
    make_ctx: Callable[..., RasterContext],
) -> None:
    """Выцветание текста снижает значение contrast."""
    check = TonalRangeCheck()

    strong = check.measure(make_ctx(ink=20))
    faded = check.measure(make_ctx(ink=150))

    assert strong is not None
    assert faded is not None
    assert faded < strong


def test_measure_shadow_on_background_within_tolerance(
    make_ctx: Callable[..., RasterContext],
) -> None:
    """Тень на фоне при тех же чернилах меняет значение не больше допуска."""
    check = TonalRangeCheck()

    plain = check.measure(make_ctx(ink=20))
    shadowed = check.measure(make_ctx(ink=20, shadow=0.5))

    assert plain is not None
    assert shadowed is not None
    assert abs(plain - shadowed) <= SHADOW_TOLERANCE
