import numpy as np

from core.checks.raster_context import RasterContext
from core.checks.resolution_check import ResolutionCheck
from core.models.raster_types import Raster


def _text_page(glyph_height: int) -> RasterContext:
    """Страница: сетка тёмных глифов-прямоугольников на белом фоне."""
    pixels = np.full((480, 480), 255, dtype=np.uint8)
    width = glyph_height // 2
    step_x = width * 2
    step_y = glyph_height * 2
    for top in range(20, 440 - glyph_height, step_y):
        for left in range(20, 440 - width, step_x):
            pixels[top : top + glyph_height, left : left + width] = 0
    return RasterContext(Raster(index=0, pixels=pixels))


def test_measure_grows_with_text_scale() -> None:
    """Значение растёт при увеличении масштаба текста."""
    check = ResolutionCheck()

    small = check.measure(_text_page(12))
    medium = check.measure(_text_page(24))
    large = check.measure(_text_page(48))

    assert small is not None and medium is not None and large is not None
    assert small < medium < large


def test_measure_returns_none_without_ink() -> None:
    """Страница без чернил даёт None."""
    blank = np.full((200, 200), 255, dtype=np.uint8)

    result = ResolutionCheck().measure(RasterContext(Raster(0, blank)))

    assert result is None
