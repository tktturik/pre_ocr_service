import math

import cv2
import numpy as np

from core.checks.base_check import Check
from core.checks.raster_context import RasterContext
from core.models.analysis_types import ScorePoints

# Ширина ядра расширения в высотах текста: склеивает буквы и слова строки.
_KERNEL_WIDTH_FACTOR = 3
# Меньше полос медиана по ним ничего не говорит о наклоне страницы.
_MIN_BANDS = 3
# Полоса с нулевой площадью контура не даёт моментов.
_MIN_MOMENT_AREA = 1e-6
# Полосы круче этого угла — не строки текста.
_MAX_ANGLE = 45.0


def _band_angles_and_lengths(mask: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Углы главных осей полос в градусах и их длины (корень главного момента).

    Угол считается по центральным моментам контура полосы, знак не используется.
    Полосы круче `_MAX_ANGLE` отбрасываются.
    """
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    angles: list[float] = []
    lengths: list[float] = []
    for contour in contours:
        moments = cv2.moments(contour)
        area = moments["m00"]
        if area < _MIN_MOMENT_AREA:
            continue
        mu20 = moments["mu20"] / area
        mu02 = moments["mu02"] / area
        mu11 = moments["mu11"] / area
        angle = math.degrees(0.5 * math.atan2(2 * mu11, mu20 - mu02))
        if abs(angle) > _MAX_ANGLE:
            continue
        major = (mu20 + mu02) / 2 + math.hypot((mu20 - mu02) / 2, mu11)
        angles.append(angle)
        lengths.append(math.sqrt(major))
    return np.array(angles), np.array(lengths)


def _weighted_median(values: np.ndarray, weights: np.ndarray) -> float:
    """Взвешенная медиана: первое значение, где накопленный вес достиг половины."""
    order = np.argsort(values)
    cumulative = np.cumsum(weights[order])
    index = int(np.searchsorted(cumulative, cumulative[-1] / 2))
    return float(values[order][index])


class SkewCheck(Check):
    """Наклон строк текста относительно горизонтали."""

    name = "skew"
    points = ScorePoints(bad=5.0, passed=3.02, good=1.0)

    def measure(self, ctx: RasterContext) -> float | None:
        """Модуль угла строк в градусах (0..45), меньше — лучше.

        Маска чернил расширяется по горизонтали ядром около трёх высот текста,
        строки сливаются в полосы; угол каждой полосы берётся по моментам её
        контура, результат — медиана углов, взвешенная по длине полос. Знак
        угла не важен. Возвращает None, если нет чернил или полос меньше трёх.
        """
        text_height = ctx.text_height
        if ctx.ink_mask is None or text_height is None:
            return None
        width = max(1, round(_KERNEL_WIDTH_FACTOR * text_height))
        kernel = np.ones((1, width), dtype=np.uint8)
        bands = cv2.dilate(ctx.ink_mask, kernel)
        angles, lengths = _band_angles_and_lengths(bands)
        if angles.size < _MIN_BANDS:
            return None
        return abs(_weighted_median(angles, lengths))


CHECK = SkewCheck()
