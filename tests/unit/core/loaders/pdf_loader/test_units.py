import math

import pypdfium2 as pdfium
import pytest

from core.errors import TooManyPagesError
from core.loaders.pdf_loader import PdfLoader, _main_image_dpi
from core.models.analysis_types import AnalysisLimits
from core.models.raster_types import Raster

POINTS_PER_INCH = 72


def test_units_renders_page_with_main_image_density(
    pdf_from_png_96dpi_bytes: bytes, limits: AnalysisLimits
) -> None:
    """Ширина растра равна ceil(width_pt * dpi / 72) и больше ширины в пунктах."""
    pdf = pdfium.PdfDocument(pdf_from_png_96dpi_bytes)
    page = pdf[0]
    width_pt = page.get_width()
    dpi = _main_image_dpi(page)
    page.close()
    pdf.close()

    units = list(PdfLoader().units(pdf_from_png_96dpi_bytes, limits))

    assert dpi is not None
    assert dpi == pytest.approx(96, abs=1)
    assert isinstance(units[0], Raster)
    width_px = units[0].pixels.shape[1]
    assert width_px == math.ceil(width_pt * dpi / POINTS_PER_INCH)
    assert width_px > width_pt


def test_units_rejects_pdf_over_page_limit(
    two_page_pdf_bytes: bytes, one_page_limits: AnalysisLimits
) -> None:
    """Превышение лимита страниц даёт TooManyPagesError до первого растра."""
    units = PdfLoader().units(two_page_pdf_bytes, one_page_limits)

    with pytest.raises(TooManyPagesError):
        next(units)
