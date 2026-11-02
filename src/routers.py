import logging

from fastapi import APIRouter, FastAPI, Response, status

logger = logging.getLogger(__name__)

health_router = APIRouter()


@health_router.get("/health", status_code=status.HTTP_204_NO_CONTENT)
async def health() -> Response:
    """Проверка живости сервиса."""
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def get_routers() -> list[APIRouter]:
    """
    Возвращает список маршрутов для подключения к приложению.
    """
    return [health_router]


def setup_routers(app: FastAPI) -> None:
    """
    Подключает все маршруты к приложению и логирует их инициализацию.
    """
    for router in get_routers():
        app.include_router(router)
