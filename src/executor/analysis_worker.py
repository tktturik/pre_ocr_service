import time
from collections.abc import Sequence

from loguru import logger

from config.log_context import page_var
from core.checks.base_check import Check
from core.checks.raster_context import RasterContext
from core.loaders.base_loader import Loader, select_loader
from core.models.analysis_types import (
    AnalysisRequest,
    CheckOutcome,
    ItemResult,
    Verdict,
    WorkerResult,
)
from core.models.raster_types import Raster, UnitError
from core.registry import Registry
from core.scoring.check_scoring import make_outcome
from core.scoring.raster_scoring import score_raster

# Хватает самой длинной сигнатуры формата (PNG, 8 байт) с запасом.
_HEAD_SIZE = 16


class AnalysisWorker:
    """Оркестрация внутри воркера: формат, загрузчик, проверки, скоринг."""

    def __init__(self, checks: Registry[Check], loaders: Sequence[Loader]) -> None:
        self._checks = checks
        self._loaders = loaders

    def run(self, request: AnalysisRequest) -> WorkerResult:
        """Анализирует документ и возвращает результаты по его единицам.

        Ошибка единицы или проверки не прерывает задачу (D26, D27).
        Ошибки уровня документа (`InputError`) пробрасываются.
        """
        started = time.perf_counter()
        loader = select_loader(request.data[:_HEAD_SIZE], self._loaders)
        items: list[ItemResult] = []
        for unit in loader.units(request.data, request.limits):
            token = page_var.set(unit.index)
            try:
                if isinstance(unit, UnitError):
                    logger.warning("Unit failed to load: {}", unit.reason)
                    items.append(self._failed_item(unit.index))
                else:
                    items.append(self._analyze(unit, request.checks))
            finally:
                page_var.reset(token)
            # Растр освобождается до загрузки следующей единицы.
            del unit
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        return WorkerResult(items=tuple(items), processing_time_ms=elapsed_ms)

    @staticmethod
    def _failed_item(index: int) -> ItemResult:
        """Единица, которую не удалось загрузить: непригодна со скором 0 (D26)."""
        return ItemResult(index=index, verdict=Verdict(False, 0.0), checks=())

    def _analyze(self, raster: Raster, check_names: tuple[str, ...]) -> ItemResult:
        """Прогоняет запрошенные проверки по растру и считает вердикт единицы."""
        ctx = RasterContext(raster)
        outcomes = tuple(self._run_check(name, ctx) for name in check_names)
        return ItemResult(
            index=raster.index, verdict=score_raster(outcomes), checks=outcomes
        )

    def _run_check(self, name: str, ctx: RasterContext) -> CheckOutcome:
        """Исход одной проверки; неожиданное исключение даёт провал (D27)."""
        check = self._checks.get(name)
        try:
            value = check.measure(ctx)
        except Exception:  # noqa: BLE001  # сбой проверки не роняет задачу
            logger.exception("Check {} raised an exception", name)
            return CheckOutcome(name=name, passed=False, score=0.0, value=None)
        return make_outcome(name, value, check.points)
