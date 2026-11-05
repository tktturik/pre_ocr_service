from collections.abc import Callable

import cv2
import numpy as np
import pytest

from core.checks.raster_context import RasterContext
from core.models.raster_types import Raster


@pytest.fixture
def make_ctx() -> Callable[..., RasterContext]:
    """Фабрика контекста: чёрный текст на белом, размытый по Гауссу."""

    def factory(sigma: float) -> RasterContext:
        page = np.full((120, 360), 255, dtype=np.uint8)
        for line, text in enumerate(("Hello OCR 2024", "Sharp text")):
            cv2.putText(
                page,
                text,
                (15, 45 + 50 * line),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                0,
                1,
                cv2.LINE_AA,
            )
        blurred = cv2.GaussianBlur(page, (0, 0), sigma)
        return RasterContext(Raster(index=0, pixels=blurred))

    return factory
