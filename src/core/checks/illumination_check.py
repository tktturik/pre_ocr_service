import numpy as np

from core.checks.base_check import Check
from core.checks.raster_context import RasterContext
from core.models.analysis_types import ScorePoints

_EDGE_PERCENTILE = 5  # доля площади карты фона у каждого края, в процентах


class IlluminationCheck(Check):
    """Неравномерность освещения: отклонение краёв карты фона от медианы."""

    name = "illumination"
    points = ScorePoints(bad=0.4, passed=0.25, good=0.15)

    def measure(self, ctx: RasterContext) -> float | None:
        """Большее из отклонений тёмного и светлого краёв фона, в долях медианы."""
        median = ctx.background_level
        background = ctx.background
        dark = float(np.percentile(background, _EDGE_PERCENTILE))
        bright = float(np.percentile(background, 100 - _EDGE_PERCENTILE))
        return max(abs(dark - median), abs(bright - median)) / median


CHECK = IlluminationCheck()
