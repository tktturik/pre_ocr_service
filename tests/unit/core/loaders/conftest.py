import io
import random

import pytest
from PIL import Image

from core.models.analysis_types import AnalysisLimits


@pytest.fixture
def limits() -> AnalysisLimits:
    """Лимиты без практического ограничения растра."""
    return AnalysisLimits(
        max_raster_pixels=100_000_000, max_pdf_pages=10, pdf_fallback_dpi=150
    )


@pytest.fixture
def pdf_from_png_96dpi_bytes() -> bytes:
    """PDF из одного серого изображения 150x100, сохранённого Pillow с 96 dpi."""
    buffer = io.BytesIO()
    Image.new("L", (150, 100), color=128).save(buffer, format="PDF", resolution=96)
    return buffer.getvalue()


@pytest.fixture
def tight_pixel_limits() -> AnalysisLimits:
    """Лимит растра на пиксель меньше корневого png_bytes 16x16."""
    return AnalysisLimits(
        max_raster_pixels=255, max_pdf_pages=10, pdf_fallback_dpi=150
    )


@pytest.fixture
def truncated_png_bytes() -> bytes:
    """PNG 64x64 с шумом: заголовок цел, данные пикселей обрезаны."""
    noise = random.Random(0).randbytes(64 * 64)
    buffer = io.BytesIO()
    Image.frombytes("L", (64, 64), noise).save(buffer, format="PNG")
    data = buffer.getvalue()
    return data[: len(data) // 2]


@pytest.fixture
def two_page_pdf_bytes() -> bytes:
    """PDF из двух серых изображений."""
    first = Image.new("L", (50, 50), color=100)
    second = Image.new("L", (50, 50), color=200)
    buffer = io.BytesIO()
    first.save(buffer, format="PDF", save_all=True, append_images=[second])
    return buffer.getvalue()


@pytest.fixture
def one_page_limits() -> AnalysisLimits:
    """Лимит в одну страницу PDF."""
    return AnalysisLimits(
        max_raster_pixels=100_000_000, max_pdf_pages=1, pdf_fallback_dpi=150
    )
