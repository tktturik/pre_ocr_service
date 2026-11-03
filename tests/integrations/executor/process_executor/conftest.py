from collections.abc import AsyncIterator
from pathlib import Path

import pytest

from config.settings.analysis import AnalysisSettings
from config.settings.logger import LoggerSettings
from core.checks.base_check import build_check_registry
from core.loaders.image_loader import ImageLoader
from core.models.analysis_types import AnalysisLimits, AnalysisRequest
from executor.admission_limiter import AdmissionLimiter
from executor.analysis_worker import AnalysisWorker
from executor.process_executor import ProcessExecutor
from executor.worker_types import WorkerConfig

CHECK_MODULES = (
    "tests.fakes.constant_check",
    "tests.fakes.sleep_check",
    "tests.fakes.crash_check",
)
PROJECT_ROOT = Path(__file__).resolve().parents[4]


@pytest.fixture
def analysis_settings() -> AnalysisSettings:
    """Пул из одного процесса, один в очереди, малый таймаут задачи."""
    return AnalysisSettings(
        pool_size=1,
        queue_size=1,
        task_timeout_s=1.0,
        start_method="spawn",
        check_modules=CHECK_MODULES,
    )


@pytest.fixture
def worker_config() -> WorkerConfig:
    """Конфиг воркера с пустышками constant, sleep, crash."""
    return WorkerConfig(
        check_modules=CHECK_MODULES,
        logger=LoggerSettings(),
        project_root=PROJECT_ROOT,
    )


@pytest.fixture
def limiter(analysis_settings: AnalysisSettings) -> AdmissionLimiter:
    """Лимит входа на N + M слотов."""
    return AdmissionLimiter(
        running=analysis_settings.pool_size, waiting=analysis_settings.queue_size
    )


@pytest.fixture
async def executor(
    analysis_settings: AnalysisSettings,
    worker_config: WorkerConfig,
    limiter: AdmissionLimiter,
) -> AsyncIterator[ProcessExecutor]:
    """Запущенный исполнитель с реальным пулом spawn; останавливается после теста."""
    process_executor = ProcessExecutor(analysis_settings, worker_config, limiter)
    await process_executor.start()
    yield process_executor
    await process_executor.stop()


@pytest.fixture
def limits() -> AnalysisLimits:
    """Лимиты с запасом для малых растров."""
    return AnalysisLimits(
        max_raster_pixels=1_000_000, max_pdf_pages=10, pdf_fallback_dpi=100
    )


@pytest.fixture
def constant_request(png_bytes: bytes, limits: AnalysisLimits) -> AnalysisRequest:
    """Запрос с PNG и проверкой constant."""
    return AnalysisRequest("rid", png_bytes, ("constant",), limits)


@pytest.fixture
def sleep_request(png_bytes: bytes, limits: AnalysisLimits) -> AnalysisRequest:
    """Запрос с PNG и проверкой sleep."""
    return AnalysisRequest("rid", png_bytes, ("sleep",), limits)


@pytest.fixture
def crash_request(png_bytes: bytes, limits: AnalysisLimits) -> AnalysisRequest:
    """Запрос с PNG и проверкой crash."""
    return AnalysisRequest("rid", png_bytes, ("crash",), limits)


@pytest.fixture
def direct_worker() -> AnalysisWorker:
    """Воркер в процессе теста: эталон для сравнения с результатом пула."""
    registry = build_check_registry(["tests.fakes.constant_check"])
    return AnalysisWorker(registry, [ImageLoader()])
