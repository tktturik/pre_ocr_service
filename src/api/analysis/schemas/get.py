from pydantic import BaseModel


class ChecksResponse(BaseModel):
    """Тело ответа `GET /checks`: имена проверок из реестра."""

    checks: list[str]
