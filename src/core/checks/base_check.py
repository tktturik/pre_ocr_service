import importlib
from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import ClassVar

from core.checks.raster_context import RasterContext
from core.models.analysis_types import ScorePoints
from core.registry import Registry


class Check(ABC):
    """Проверка растра: одна измеряемая величина и опорные точки её шкалы.

    Модуль проверки экспортирует экземпляр в `CHECK`; имя проверки уникально в реестре.
    """

    name: ClassVar[str]
    points: ClassVar[ScorePoints]

    @abstractmethod
    def measure(self, ctx: RasterContext) -> float | None:
        """Возвращает измеренное значение или None, если измерить нельзя."""


def build_check_registry(module_names: Sequence[str]) -> Registry[Check]:
    """Собирает реестр проверок из модулей, перечисленных по имени,
    по атрибуту `CHECK` каждого.

    Повторное имя проверки приводит к `ValueError` из реестра.
    """
    registry = Registry[Check]("check")
    for module_name in module_names:
        check = importlib.import_module(module_name).CHECK
        registry.register(check.name, check)
    return registry
