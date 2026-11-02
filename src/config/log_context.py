from contextvars import ContextVar

request_id_var: ContextVar[str] = ContextVar("request_id", default="-")
page_var: ContextVar[int | None] = ContextVar("page", default=None)
