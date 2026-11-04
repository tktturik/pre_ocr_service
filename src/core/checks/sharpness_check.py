"""Проверка резкости: σ размытия края, делённое на высоту текста."""

from typing import ClassVar

import cv2
import numpy as np

from core.checks.base_check import Check
from core.checks.raster_context import RasterContext
from core.models.analysis_types import ScorePoints

_EDGE_KERNEL = np.ones((3, 3), np.uint8)
_SOBEL_NORM = 8.0  # сумма весов ядра Собеля 3x3: приводит отклик к градиенту
_GRADIENT_PERCENTILE = 90  # «сильные» градиенты на границе маски
_MIN_EDGE_CONTRAST = 1.0  # меньший разрыв фона и чернил считается отсутствием края


class SharpnessCheck(Check):
    """σ размытия края / H: чем больше значение, тем сильнее размыт текст."""

    name: ClassVar[str] = "blur"
    # Provisional: сняты на синтетике (σ/H: 0.04 резкий, 0.06 при σ=2px,
    # 0.11 при σ=4px, H=20); утверждает владелец. Обратное направление.
    points: ClassVar[ScorePoints] = ScorePoints(bad=0.11, passed=0.08, good=0.05)

    def measure(self, ctx: RasterContext) -> float | None:
        """Возвращает ширину размытия края, делённую на высоту текста.

        Край буквы - скачок от яркости фона к яркости чернил. Чем сильнее
        размытие, тем положе склон: макс. крутизна ≈ C / (σ·√(2π)), где C -
        перепад яркости фона и чернил. Крутизну берём по границе маски
        (90-й перцентиль градиента) и находим σ. None, если измерить нельзя.
        """
        mask = ctx.ink_mask
        text_height = ctx.text_height
        if mask is None or text_height is None:
            return None
        contrast = ctx.background_level - (ctx.ink_level or 0.0)
        if contrast < _MIN_EDGE_CONTRAST:
            return None
        edge = cv2.dilate(mask, _EDGE_KERNEL) != cv2.erode(mask, _EDGE_KERNEL)
        gray = ctx.gray.astype(np.float32)
        grad_x = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3) / _SOBEL_NORM
        grad_y = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3) / _SOBEL_NORM
        magnitude = np.hypot(grad_x, grad_y)[edge]
        if magnitude.size == 0:
            return None
        gradient = float(np.percentile(magnitude, _GRADIENT_PERCENTILE))
        if gradient <= 0.0:
            return None
        sigma = contrast / (gradient * np.sqrt(2 * np.pi))
        return float(sigma / text_height)


CHECK = SharpnessCheck()
