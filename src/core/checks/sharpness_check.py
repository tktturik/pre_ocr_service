"""Проверка резкости: σ размытия края в пикселях."""

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
    """σ размытия края в пикселях: чем больше значение, тем сильнее размыт текст."""

    name: ClassVar[str] = "blur"
    points: ClassVar[ScorePoints] = ScorePoints(bad=2.4, passed=1.8, good=1.0)

    def measure(self, ctx: RasterContext) -> float | None:
        """Возвращает значение, монотонно растущее с σ размытия края в пикселях.

        Край буквы - скачок от яркости фона к яркости чернил. Чем сильнее
        размытие, тем положе склон: макс. крутизна ≈ C / (σ·√(2π)), где C -
        перепад яркости фона и чернил. Крутизну берём по границе маски
        (90-й перцентиль градиента) и находим σ. Высоту текста не делим:
        она растёт от размытия, и σ/H не отличает размытый текст (D54).

        Значение не равно σ (дно ~0.8 px от дискретизации, наклон ~0.5)
        и зависит от толщины штриха: при одном σ разница до ~0.3 px.
        None, если измерить нельзя.
        """
        mask = ctx.ink_mask
        if mask is None:
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
        return float(sigma)


CHECK = SharpnessCheck()
