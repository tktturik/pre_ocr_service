"""Проверка-пустышка: аварийно завершает процесс воркера."""

import os
from typing import ClassVar

from core.checks.base_check import Check
from core.checks.raster_context import RasterContext
from core.models.analysis_types import ScorePoints


class CrashCheck(Check):
    """Измерение убивает процесс без исключения и без очистки."""

    name: ClassVar[str] = "crash"
    points: ClassVar[ScorePoints] = ScorePoints(bad=0.0, passed=0.5, good=1.0)

    def measure(self, ctx: RasterContext) -> float | None:
        """Завершает процесс через `os._exit(1)`."""
        os._exit(1)


CHECK = CrashCheck()
