from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from loguru import logger

from request_middleware import REQUEST_ID_HEADER
from config.log_context import request_id_var
from core.errors import (
    AnalysisError,
    AnalysisTimeoutError,
    InputError,
    InvalidRequestError,
    OverloadedError,
    UnknownChecksError,
)

INTERNAL_ERROR_CODE = "internal_error"


def _request_id(request: Request) -> str:
    """request_id из `request.state`; для необработанных исключений contextvar уже сброшен."""
    return getattr(request.state, "request_id", request_id_var.get())


def _status_for(exc: AnalysisError) -> int:
    if isinstance(exc, InputError):
        return 400
    if isinstance(exc, OverloadedError):
        return 503
    if isinstance(exc, AnalysisTimeoutError):
        return 504
    return 500


def _details(exc: AnalysisError) -> dict[str, list[str]] | None:
    if isinstance(exc, UnknownChecksError):
        return {"unknown": list(exc.args[0]), "available": list(exc.args[1])}
    return None


def _error_response(
    request: Request, status_code: int, code: str, details: object = None
) -> JSONResponse:
    request_id = _request_id(request)
    headers = {REQUEST_ID_HEADER: request_id}
    if status_code == 503:
        headers["Retry-After"] = "1"
    return JSONResponse(
        status_code=status_code,
        content={"code": code, "request_id": request_id, "details": details},
        headers=headers,
    )


def setup_exception_handlers(app: FastAPI) -> None:
    """Регистрирует перевод ошибок core и необработанных исключений в HTTP-ответы."""

    @app.exception_handler(AnalysisError)
    async def analysis_error_handler(
        request: Request, exc: AnalysisError
    ) -> JSONResponse:
        status_code = _status_for(exc)
        if isinstance(exc, InputError):
            logger.warning("Input rejected: code={}", exc.code)
        elif exc.code == INTERNAL_ERROR_CODE:
            logger.opt(exception=exc).error("Internal error")
        return _error_response(request, status_code, exc.code, _details(exc))

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        logger.warning("Input rejected: code={}", InvalidRequestError.code)
        return _error_response(request, 400, InvalidRequestError.code)

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        """Необработанное исключение: лог со стеком, ответ без текста и типа исключения."""
        logger.exception(
            "Unhandled {} in API endpoint\nAPI endpoint: {}\nMethod: {}",
            exc.__class__.__name__,
            request.url.path,
            request.method,
        )
        return _error_response(request, 500, INTERNAL_ERROR_CODE)
