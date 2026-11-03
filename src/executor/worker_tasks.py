import importlib
import os

import cv2

from config.log_conf import setup_logging
from config.log_context import request_id_var
from core.checks.base_check import build_check_registry
from core.loaders.base_loader import Loader
from core.models.analysis_types import AnalysisRequest, WorkerResult
from executor.analysis_worker import AnalysisWorker
from executor.worker_types import WorkerConfig

LOADER_MODULES: tuple[str, ...] = (
    "core.loaders.pdf_loader",
    "core.loaders.image_loader",
)

_WORKER_NICE = 10


def init_worker(config: WorkerConfig) -> None:
    """Инициализатор процесса пула: потоки cv2, приоритет, логи, импорт проверок.

    Импорт модулей проверок здесь прогревает воркер до первого запроса.
    """
    cv2.setNumThreads(1)
    os.nice(_WORKER_NICE)
    setup_logging(config.logger, enqueue=False, project_root=config.project_root)
    for module_name in (*LOADER_MODULES, *config.check_modules):
        importlib.import_module(module_name)


def ping() -> bool:
    """Пустая задача для прогрева пула; возвращает True."""
    return True


def _load_loaders() -> tuple[Loader, ...]:
    """Загрузчики из `LOADER_MODULES` по атрибуту `LOADER` модуля."""
    return tuple(importlib.import_module(name).LOADER for name in LOADER_MODULES)


def run_analysis_task(
    request: AnalysisRequest, check_modules: tuple[str, ...]
) -> WorkerResult:
    """Задача воркера: строит реестры и выполняет анализ запроса.

    Ошибки входных данных (`InputError`) пробрасываются вызывающему.
    """
    token = request_id_var.set(request.request_id)
    try:
        worker = AnalysisWorker(build_check_registry(check_modules), _load_loaders())
        return worker.run(request)
    finally:
        request_id_var.reset(token)
