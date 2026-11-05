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
