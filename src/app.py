import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from config import settings
from config.settings.analysis import AnalysisSettings
from config.settings.logger import LoggerSettings
from core.checks.base_check import build_check_registry
from exc_handlers import setup_exception_handlers
from executor.admission_limiter import AdmissionLimiter
from executor.process_executor import ProcessExecutor
from executor.worker_types import WorkerConfig
from request_middleware import setup_request_middleware
from routers import setup_routers
from services.analysis_service import AnalysisService

logger = logging.getLogger(__name__)


def create_app(
    analysis_settings: AnalysisSettings | None = None,
    logger_settings: LoggerSettings | None = None,
) -> FastAPI:
    """Фабрика приложения.

    `None` в настройках означает значения из `config.settings`.
    """
    analysis_settings = analysis_settings or settings.analysis
    logger_settings = logger_settings or settings.logger

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        logger.info("START Application")
        registry = build_check_registry(analysis_settings.check_modules)
        app.state.check_names = registry.names()
        worker_config = WorkerConfig(
            check_modules=analysis_settings.check_modules,
            logger=logger_settings,
            project_root=Path(__file__).resolve().parent.parent,
        )
        limiter = AdmissionLimiter(
            analysis_settings.pool_size, analysis_settings.queue_size
        )
        executor = ProcessExecutor(analysis_settings, worker_config, limiter)
        # Сбой прогрева пробрасывается: приложение не стартует.
        await executor.start()
        app.state.analysis_service = AnalysisService(executor)
        try:
            yield
        finally:
            await executor.stop()
        logger.info("FINISH Application")

    app = FastAPI(lifespan=lifespan, redirect_slashes=False)
    app.state.analysis_settings = analysis_settings
    app.state.logger_settings = logger_settings
    setup_exception_handlers(app)
    setup_request_middleware(app)
    setup_routers(app)
    return app
