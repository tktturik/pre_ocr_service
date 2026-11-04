from collections.abc import Callable

import cv2
import numpy as np
import pytest

from core.checks.raster_context import RasterContext
from core.checks.sharpness_check import SharpnessCheck
from core.models.raster_types import Raster
from core.scoring.check_scoring import score_value

# Допуск сценария 2: разница значений при масштабе x1 и x2 (абсолютная).
# По замерам реализации для размытого текста (sigma >= 1.5, sigma растёт
# вместе с текстом) расхождение около 0.01; допуск с небольшим запасом и
# заметно меньше шага шкалы 0.05 / 0.08 / 0.11.
SCALE_TOLERANCE = 0.015


@pytest.fixture
def make_ctx() -> Callable[..., RasterContext]:
    """Фабрика контекста: чёрный текст на белом, размытый по Гауссу."""

    def factory(sigma: float, scale: int = 1) -> RasterContext:
        page = np.full((120 * scale, 360 * scale), 255, dtype=np.uint8)
        for line, text in enumerate(("Hello OCR 2024", "Sharp text")):
            cv2.putText(
                page,
                text,
                (15 * scale, (45 + 50 * line) * scale),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9 * scale,
                0,
                scale,
                cv2.LINE_AA,
            )
        # Размытие масштабируется вместе с текстом (sigma задана для x1).
        blurred = cv2.GaussianBlur(page, (0, 0), sigma * scale)
        return RasterContext(Raster(index=0, pixels=blurred))

    return factory


def test_measure_stronger_blur_lowers_score(
    make_ctx: Callable[..., RasterContext],
) -> None:
    """Рост sigma размытия увеличивает значение и монотонно снижает скор."""
    check = SharpnessCheck()

    sharp, soft, blurry = (check.measure(make_ctx(sigma=s)) for s in (1, 3, 5))

    assert sharp is not None
    assert soft is not None
    assert blurry is not None
    assert sharp < soft < blurry
    scores = [score_value(v, SharpnessCheck.points) for v in (sharp, soft, blurry)]
    assert scores[0] >= scores[1] >= scores[2]
    assert scores[0] > scores[2]


@pytest.mark.parametrize("sigma", [1.5, 3.0])
def test_measure_value_independent_of_scale(
    make_ctx: Callable[..., RasterContext], sigma: float
) -> None:
    """Значение размытого текста при масштабе x1 и x2 совпадает с допуском."""
    check = SharpnessCheck()

    at_1x = check.measure(make_ctx(sigma=sigma, scale=1))
    at_2x = check.measure(make_ctx(sigma=sigma, scale=2))

    assert at_1x is not None
    assert at_2x is not None
    assert abs(at_1x - at_2x) <= SCALE_TOLERANCE
