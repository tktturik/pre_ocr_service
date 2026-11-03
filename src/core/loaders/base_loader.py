from abc import ABC, abstractmethod
from collections.abc import Iterator, Sequence
from typing import ClassVar

from core.errors import UnsupportedFormatError
from core.models.analysis_types import AnalysisLimits
from core.models.raster_types import Unit


class Loader(ABC):
    """Загрузчик формата: по сигнатуре узнаёт свой формат и отдаёт единицы документа."""

    name: ClassVar[str]

    @abstractmethod
    def matches(self, head: bytes) -> bool:
        """Узнаёт формат по первым байтам файла; данные не декодирует."""

    @abstractmethod
    def units(self, data: bytes, limits: AnalysisLimits) -> Iterator[Unit]:
        """Отдаёт единицы документа (растры или ошибки единиц) в порядке следования."""


def select_loader(head: bytes, loaders: Sequence[Loader]) -> Loader:
    """Возвращает первый загрузчик, чья сигнатура подошла.

    Ошибка: UnsupportedFormatError, если ни один загрузчик не подошёл.
    """
    for loader in loaders:
        if loader.matches(head):
            return loader
    raise UnsupportedFormatError()
