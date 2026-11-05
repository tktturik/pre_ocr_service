from collections.abc import Callable

import numpy as np
import pytest

from core.checks.raster_context import RasterContext
from core.models.raster_types import Raster

MARGIN = 64
PAPER = 255
SEED = 0


@pytest.fixture
def make_noisy_ctx(
    page_raster_factory: Callable[[int, int], Raster],
) -> Callable[..., RasterContext]:
    """Фабрика шумной страницы: make(sigma, fade=1.0) -> RasterContext."""

    def make(sigma: float, fade: float = 1.0) -> RasterContext:
        page = page_raster_factory(glyph_height=12, ink_value=30).pixels
        framed = np.pad(page, MARGIN, constant_values=PAPER)
        # Фиксированное зерно: шум одинаков при разных fade.
        rng = np.random.default_rng(SEED)
        noisy = framed.astype(np.float64) + rng.normal(0.0, sigma, framed.shape)
        pixels = np.clip(noisy, 0, 255).astype(np.uint8)
        faded = PAPER - (PAPER - pixels.astype(np.float64)) * fade
        faded_pixels = np.clip(np.rint(faded), 0, 255).astype(np.uint8)
        return RasterContext(Raster(index=0, pixels=faded_pixels))

    return make
