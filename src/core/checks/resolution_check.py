"""Проверка разрешения: высота текста в пикселях."""

from typing import ClassVar

from core.checks.base_check import Check
from core.checks.raster_context import RasterContext
from core.models.analysis_types import ScorePoints


class ResolutionCheck(Check):
    """Медиана высоты компонент чернил; мелкий текст даёт малое значение."""

    name: ClassVar[str] = "resolution"
    points: ClassVar[ScorePoints] = ScorePoints(bad=8.0, passed=12.0, good=20.0)

    def measure(self, ctx: RasterContext) -> float | None:
        """Возвращает высоту текста в пикселях или None, если чернил нет."""
        return ctx.text_height


CHECK = ResolutionCheck()
