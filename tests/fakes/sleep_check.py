"""Проверка-пустышка: спит дольше таймаута задачи в integration-тестах."""

import time
from typing import ClassVar

from core.checks.base_check import Check
from core.checks.raster_context import RasterContext
from core.models.analysis_types import ScorePoints

SLEEP_SECONDS = 10.0


class SleepCheck(Check):
    """Измерение длится `SLEEP_SECONDS`, заведомо дольше `task_timeout_s` фикстуры."""

    name: ClassVar[str] = "sleep"
    points: ClassVar[ScorePoints] = ScorePoints(bad=0.0, passed=0.5, good=1.0)

    def measure(self, ctx: RasterContext) -> float | None:
        """Спит `SLEEP_SECONDS` и возвращает значение выше точки passed."""
        time.sleep(SLEEP_SECONDS)
        return 0.9


CHECK = SleepCheck()
