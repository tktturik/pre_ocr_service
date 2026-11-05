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
        page = np.full((700, 900), 255, dtype=np.uint8)
        # Крупный шрифт и разрежённые буквы: при σ 5 компоненты не склеиваются,
        # букв-компонент остаётся заметно больше порога 20.
        lines = ("H e l l o  O C R  2 0 2 6", "S h a r p  t e x t") * 3
        for line, text in enumerate(lines):
            cv2.putText(
                page,
                text,
                (15, 60 + 80 * line),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.4,
                0,
                2,
                cv2.LINE_AA,
            )
        blurred = cv2.GaussianBlur(page, (0, 0), sigma)
        return RasterContext(Raster(index=0, pixels=blurred))

    return factory
