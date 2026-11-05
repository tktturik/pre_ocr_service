import numpy as np
import pytest

from core.checks.raster_context import RasterContext
from core.models.raster_types import Raster

PAGE_SIZE = 400
BACKGROUND = 240.0
INK = 30
GRAY_BACKGROUND = 150.0


def _draw_text(page: np.ndarray, col_from: int, col_to: int) -> None:
    """Рисует строки глифов-прямоугольников в полосе столбцов [col_from, col_to)."""
    for row in range(30, 370, 30):
        for col in range(col_from, col_to, 12):
            page[row : row + 14, col : col + 6] = INK


def _context(page: np.ndarray) -> RasterContext:
    """Собирает контекст растра из страницы с плавающей точкой."""
    pixels = np.clip(page, 0, 255).astype(np.uint8)
    return RasterContext(Raster(index=0, pixels=pixels))


@pytest.fixture
def shadow_without_text_ctx() -> RasterContext:
    """Текст только слева; справа, без текста, спад яркости от 1.0 до 0.3."""
    page = np.full((PAGE_SIZE, PAGE_SIZE), BACKGROUND)
    _draw_text(page, 20, PAGE_SIZE // 2 - 20)
    half = PAGE_SIZE // 2
    page[:, half:] *= np.linspace(1.0, 0.3, PAGE_SIZE - half)[None, :]
    return _context(page)


@pytest.fixture
def gray_fill_ctx() -> RasterContext:
    """Белая страница с текстом и серый прямоугольник (~20%) с текстом внутри."""
    page = np.full((PAGE_SIZE, PAGE_SIZE), BACKGROUND)
    # Сторона 180 из 400: площадь 20.25% страницы.
    page[110:290, 110:290] = GRAY_BACKGROUND
    _draw_text(page, 20, 380)
    return _context(page)
