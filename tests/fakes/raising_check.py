"""Проверка-пустышка: всегда падает с RuntimeError."""

from typing import ClassVar

from core.checks.base_check import Check
from core.checks.raster_context import RasterContext
from core.models.analysis_types import ScorePoints


class RaisingCheck(Check):
    """Измерение завершается исключением."""

    name: ClassVar[str] = "raising"
    points: ClassVar[ScorePoints] = ScorePoints(bad=0.0, passed=0.5, good=1.0)

    def measure(self, ctx: RasterContext) -> float | None:
        """Бросает RuntimeError."""
        raise RuntimeError("boom")


CHECK = RaisingCheck()
