from typing import Annotated

from fastapi import Depends, Query, Request

from config.settings.analysis import AnalysisSettings
from core.errors import (
    EmptyChecksError,
    FileTooLargeError,
    InvalidRequestError,
    UnknownChecksError,
)
from services.analysis_service import AnalysisService


def get_service(request: Request) -> AnalysisService:
    """Сервис анализа, созданный в lifespan."""
    return request.app.state.analysis_service


def get_check_names(request: Request) -> tuple[str, ...]:
    """Имена зарегистрированных проверок в порядке регистрации."""
    return request.app.state.check_names


def get_analysis_settings(request: Request) -> AnalysisSettings:
    """Настройки анализа, переданные в `create_app`."""
    return request.app.state.analysis_settings


def get_requested_checks(
    checks: Annotated[str, Query()],
    check_names: Annotated[tuple[str, ...], Depends(get_check_names)],
) -> tuple[str, ...]:
    """Разбирает `checks` через запятую: без пробелов и дублей, порядок запроса.

    Raises:
        EmptyChecksError: в списке нет ни одного имени.
        UnknownChecksError: есть имена, которых нет среди зарегистрированных.
    """
    names = dict.fromkeys(part.strip() for part in checks.split(","))
    names.pop("", None)
    if not names:
        raise EmptyChecksError("empty_checks")
    requested = tuple(names)
    unknown = tuple(name for name in requested if name not in check_names)
    if unknown:
        raise UnknownChecksError(unknown, check_names)
    return requested


async def get_body(
    request: Request,
    settings: Annotated[AnalysisSettings, Depends(get_analysis_settings)],
    requested: Annotated[tuple[str, ...], Depends(get_requested_checks)],
) -> bytes:
    """Читает тело запроса потоком, обрывая чтение на `max_file_bytes`.

    Параметр `requested` не используется: зависимость нужна, чтобы тело не
    читалось, если `checks` не прошли проверку.

    Raises:
        FileTooLargeError: тело больше `max_file_bytes`.
        InvalidRequestError: тело пусто или `Content-Length` не число.
    """
    max_bytes = settings.max_file_bytes
    content_length = request.headers.get("content-length")
    if content_length is not None:
        try:
            declared = int(content_length)
        except ValueError as exc:
            raise InvalidRequestError("invalid_request") from exc
        if declared > max_bytes:
            raise FileTooLargeError("file_too_large")
    body = bytearray()
    async for chunk in request.stream():
        body += chunk
        if len(body) > max_bytes:
            raise FileTooLargeError("file_too_large")
    if not body:
        raise InvalidRequestError("invalid_request")
    return bytes(body)
