from collections.abc import Awaitable, Callable
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, Request, Response
from loguru import logger

from config.log_context import request_id_var

REQUEST_ID_HEADER = "X-Request-ID"


def setup_request_middleware(app: FastAPI) -> None:
    """
    Подключает middleware: request_id в contextvar, `request.state`,
    заголовок ответа и итоговая строка лога.
    """

    @app.middleware("http")
    async def request_id_middleware(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request_id = uuid4().hex
        request.state.request_id = request_id
        token = request_id_var.set(request_id)
        try:
            start_time = perf_counter()
            response = await call_next(request)
            process_time = perf_counter() - start_time
            response.headers[REQUEST_ID_HEADER] = request_id
            # Строка пишется внутри контекста, чтобы нести request_id.
            logger.info(
                '"{} {} HTTP/{}" from {} status - {} time - {:.3f}s',
                request.method,
                request.url.path,
                request.scope["http_version"],
                getattr(request.client, "host", "unknown"),
                response.status_code,
                process_time,
            )
            return response
        finally:
            request_id_var.reset(token)
