from typing import ClassVar

import numpy as np

from core.checks.base_check import Check
from core.checks.raster_context import RasterContext
from core.models.analysis_types import ScorePoints


class TonalRangeCheck(Check):
    """Тональный диапазон: 1 − типичный уровень чернил на нормализованном сером.

    Яркость делится на фон, поэтому тень на фоне не меняет значение.
    """

    name: ClassVar[str] = "contrast"
    points: ClassVar[ScorePoints] = ScorePoints(bad=0.15, passed=0.3, good=0.5)

    def measure(self, ctx: RasterContext) -> float | None:
        """Возвращает 1 − медиану нормализованной яркости под маской чернил."""
        if ctx.ink_mask is None:
            return None
        ink_level = float(np.median(ctx.normalized[ctx.ink_mask > 0]))
        return 1.0 - ink_level


CHECK = TonalRangeCheck()
