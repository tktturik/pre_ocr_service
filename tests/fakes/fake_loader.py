"""Фиктивный загрузчик: отдаёт заранее заданные единицы."""

from collections.abc import Iterator, Sequence
from typing import ClassVar

from core.loaders.base_loader import Loader
from core.models.analysis_types import AnalysisLimits
from core.models.raster_types import Unit


class FakeLoader(Loader):
    """Принимает любые данные и отдаёт переданные единицы."""

    name: ClassVar[str] = "fake"

    def __init__(self, units: Sequence[Unit]) -> None:
        self._units = tuple(units)

    def matches(self, head: bytes) -> bool:
        """Узнаёт любой формат."""
        return True

    def units(self, data: bytes, limits: AnalysisLimits) -> Iterator[Unit]:
        """Отдаёт заданные единицы по порядку."""
        yield from self._units
