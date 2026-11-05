from collections.abc import Callable

import numpy as np
import pytest

from core.models.raster_types import Raster


@pytest.fixture
def page_raster_factory() -> Callable[[int, int], Raster]:
    """Фабрика страницы: глифы-прямоугольники заданной яркости на фоне 255."""

    def make(glyph_height: int, ink_value: int) -> Raster:
        pixels = np.full((480, 480), 255, dtype=np.uint8)
        width = glyph_height // 2
        for top in range(20, 440 - glyph_height, glyph_height * 2):
            for left in range(20, 440 - width, width * 2):
                pixels[top : top + glyph_height, left : left + width] = ink_value
        return Raster(index=0, pixels=pixels)

    return make
