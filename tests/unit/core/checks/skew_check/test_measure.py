from collections.abc import Callable

import cv2
import numpy as np
import pytest

from core.checks.raster_context import RasterContext
from core.checks.skew_check import SkewCheck
from core.models.raster_types import Raster

# Допуск из плана S4.2: значение совпадает с известным углом до 1 градуса.
ANGLE_TOLERANCE = 1.0
PAPER = 255


@pytest.fixture
def make_rotated_ctx(
    page_raster_factory: Callable[[int, int], Raster],
) -> Callable[[float], RasterContext]:
    """Фабрика страницы с глифами, повёрнутой на заданный угол в градусах."""

    def make(angle: float) -> RasterContext:
        page = page_raster_factory(24, 0).pixels
        center = (page.shape[1] / 2, page.shape[0] / 2)
        matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(
            page,
            matrix,
            (page.shape[1], page.shape[0]),
            flags=cv2.INTER_LINEAR,
            borderValue=PAPER,
        )
        return RasterContext(Raster(index=0, pixels=rotated))

    return make


@pytest.fixture
def blank_ctx() -> RasterContext:
    """Контекст чистой белой страницы без чернил."""
    pixels = np.full((480, 480), PAPER, dtype=np.uint8)
    return RasterContext(Raster(index=0, pixels=pixels))


@pytest.mark.parametrize("angle", [5.0, -5.0])
def test_skew_returns_absolute_rotation_angle(
    make_rotated_ctx: Callable[[float], RasterContext],
    angle: float,
) -> None:
    """Поворот на +-5 градусов даёт абсолютный угол около 5 без знака."""
    # Шаг строк 48 px, высота глифа 24 px: при 5 градусах горизонтальное
    # ядро слияния (~72 px) добавляет к полосе ~6 px по вертикали, итого
    # ~30 px < 48 px, поэтому соседние строки не сливаются в одну полосу.
    result = SkewCheck().measure(make_rotated_ctx(angle))

    assert result is not None
    assert abs(result - abs(angle)) <= ANGLE_TOLERANCE


def test_skew_without_ink_is_none(blank_ctx: RasterContext) -> None:
    """Страница без чернил даёт None."""
    assert SkewCheck().measure(blank_ctx) is None
