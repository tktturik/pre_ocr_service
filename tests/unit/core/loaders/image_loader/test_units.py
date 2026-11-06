import pytest

from core.errors import DocumentUnreadableError, TooManyPixelsError
from core.loaders.image_loader import ImageLoader
from core.models.analysis_types import AnalysisLimits


def test_units_rejects_image_over_pixel_limit(
    png_bytes: bytes, tight_pixel_limits: AnalysisLimits
) -> None:
    """Изображение больше лимита пикселей даёт TooManyPixelsError."""
    with pytest.raises(TooManyPixelsError):
        list(ImageLoader().units(png_bytes, tight_pixel_limits))


def test_units_rejects_truncated_image(
    truncated_png_bytes: bytes, limits: AnalysisLimits
) -> None:
    """Обрезанное изображение даёт DocumentUnreadableError."""
    with pytest.raises(DocumentUnreadableError):
        list(ImageLoader().units(truncated_png_bytes, limits))
