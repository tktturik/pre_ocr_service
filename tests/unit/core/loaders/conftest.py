import io

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
