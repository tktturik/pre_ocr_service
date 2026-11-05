import math
from collections.abc import Iterator

import numpy as np
import pypdfium2 as pdfium
import pypdfium2.raw as pdfium_raw

from core.errors import (
    DocumentUnreadableError,
    EncryptedPdfError,
    TooManyPagesError,
)
from core.loaders.base_loader import Loader
from core.models.analysis_types import AnalysisLimits
from core.models.raster_types import Raster, Unit, UnitError

PDF_SIGNATURE = b"%PDF-"
POINTS_PER_INCH = 72.0
# FPDF_GetSecurityHandlerRevision возвращает -1 у незащищённого документа.
NOT_PROTECTED_REVISION = -1
ENCRYPTION_ERR_CODES = (pdfium_raw.FPDF_ERR_PASSWORD, pdfium_raw.FPDF_ERR_SECURITY)
# Шаг уменьшения масштаба, пока округление размера битмапа вверх превышает лимит.
SCALE_SHRINK_STEP = 0.99


class PdfLoader(Loader):
    """Загрузчик PDF: отдаёт страницы серыми растрами, страница за страницей."""

    def matches(self, head: bytes) -> bool:
        """Проверяет сигнатуру PDF по первым байтам."""
        return head.startswith(PDF_SIGNATURE)

    def units(self, data: bytes, limits: AnalysisLimits) -> Iterator[Unit]:
        """Отдаёт растр или ошибку единицы на каждую страницу, индексы с 1.

        Ошибки: DocumentUnreadableError, если документ не открывается;
        EncryptedPdfError, если он зашифрован; TooManyPagesError, если страниц
        больше лимита (до первого растра). Сбой рендера страницы даёт UnitError,
        итерация продолжается.
        """
        pdf = _open_pdf(data)
        try:
            if len(pdf) > limits.max_pdf_pages:
                raise TooManyPagesError()
            for number in range(len(pdf)):
                yield _render_page(pdf, number, limits)
        finally:
            pdf.close()


def _open_pdf(data: bytes) -> pdfium.PdfDocument:
    try:
        pdf = pdfium.PdfDocument(data)
    except pdfium.PdfiumError as exc:
        if exc.err_code in ENCRYPTION_ERR_CODES:
            raise EncryptedPdfError() from exc
        raise DocumentUnreadableError() from exc
    if pdfium_raw.FPDF_GetSecurityHandlerRevision(pdf.raw) != NOT_PROTECTED_REVISION:
        pdf.close()
        raise EncryptedPdfError()
    return pdf


def _render_page(pdf: pdfium.PdfDocument, number: int, limits: AnalysisLimits) -> Unit:
    index = number + 1
    page = pdf[number]
    try:
        width, height = page.get_size()
        dpi = _main_image_dpi(page) or limits.pdf_fallback_dpi
        scale = _fit_scale(
            dpi / POINTS_PER_INCH, width, height, limits.max_raster_pixels
        )
        bitmap = page.render(scale=scale, grayscale=True) # pyright: ignore[reportArgumentType]
        try:
            # to_numpy делит память с битмапом, поэтому копируем до закрытия.
            pixels = np.array(bitmap.to_numpy(), dtype=np.uint8)
        finally:
            bitmap.close()
    except (pdfium.PdfiumError, ValueError, AssertionError) as exc:
        return UnitError(
            index=index, reason=f"page render failed: {type(exc).__name__}"
        )
    finally:
        page.close()
    return Raster(index=index, pixels=pixels)


def _main_image_dpi(page: pdfium.PdfPage) -> float | None:
    """Эффективный DPI наибольшего по площади изображения страницы; None без растров.

    Поворот и CropBox не учитываются: берётся ширина границ объекта в пунктах.
    """
    best_area = 0.0
    best_dpi: float | None = None
    for obj in page.get_objects(filter=[pdfium_raw.FPDF_PAGEOBJ_IMAGE]):
        if not isinstance(obj, pdfium.PdfImage):
            continue
        try:
            px_width, _ = obj.get_px_size()
            left, bottom, right, top = obj.get_bounds()
        except pdfium.PdfiumError:
            continue
        width_pt = right - left
        area = width_pt * (top - bottom)
        if width_pt <= 0 or area <= best_area:
            continue
        best_area = area
        best_dpi = px_width / (width_pt / POINTS_PER_INCH)
    return best_dpi


def _fit_scale(
    scale: float, width_pt: float, height_pt: float, max_pixels: int
) -> float:
    """Уменьшает масштаб так, чтобы битмап уложился в лимит."""
    scale = min(scale, math.sqrt(max_pixels / (width_pt * height_pt)))
    while math.ceil(width_pt * scale) * math.ceil(height_pt * scale) > max_pixels:
        scale *= SCALE_SHRINK_STEP
    return scale


LOADER = PdfLoader()
