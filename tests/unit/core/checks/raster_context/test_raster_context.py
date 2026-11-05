from collections.abc import Callable

from core.checks.raster_context import RasterContext
from core.models.raster_types import Raster


def test_low_contrast_ink_is_still_detected(
    page_raster_factory: Callable[[int, int], Raster],
) -> None:
    """Бледные глифы (яркость 235 на 255) дают маску чернил и высоту текста."""
    context = RasterContext(page_raster_factory(24, 235))

    assert context.ink_mask is not None
    assert context.text_height is not None


def test_blot_without_text_gives_no_ink_mask(blot_only_raster: Raster) -> None:
    """Одно пятно без букв: маски чернил нет, высота текста по Otsu есть."""
    context = RasterContext(blot_only_raster)

    assert context.ink_mask is None
    assert context.text_height is not None


def test_blot_is_excluded_from_ink_mask(text_with_blot_raster: Raster) -> None:
    """Крупное пятно не входит в маску чернил, пиксели глифов входят."""
    context = RasterContext(text_with_blot_raster)

    assert context.ink_mask is not None
    assert context.ink_mask[385, 240] == 0
    assert context.ink_mask[30, 25] == 255
