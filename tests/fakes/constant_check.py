"""Проверка-пустышка: всегда возвращает одно значение."""

from typing import ClassVar

from core.checks.base_check import Check
from core.checks.raster_context import RasterContext
from core.models.analysis_types import ScorePoints

CONSTANT_VALUE = 0.9


class ConstantCheck(Check):
    """Возвращает постоянное значение, которое лежит выше точки passed."""

    name: ClassVar[str] = "constant"
    points: ClassVar[ScorePoints] = ScorePoints(bad=0.0, passed=0.5, good=1.0)

    def measure(self, ctx: RasterContext) -> float | None:
        """Возвращает `CONSTANT_VALUE`."""
        return CONSTANT_VALUE


CHECK = ConstantCheck()
