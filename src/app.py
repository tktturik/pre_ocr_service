import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from config import settings
from config.settings.analysis import AnalysisSettings
from config.settings.logger import LoggerSettings
from exc_handlers import setup_exception_handlers
from request_middleware import setup_request_middleware

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
        yield
        logger.info("FINISH Application")

    app = FastAPI(lifespan=lifespan, redirect_slashes=False)
    app.state.analysis_settings = analysis_settings
    app.state.logger_settings = logger_settings
    setup_exception_handlers(app)
    setup_request_middleware(app)
    return app
