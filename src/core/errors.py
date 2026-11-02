from typing import ClassVar


class AnalysisError(Exception):
    """Базовая ошибка анализа; `code` уходит в тело HTTP-ошибки."""

    code: ClassVar[str]


class InputError(AnalysisError):
    """Ошибка входных данных, HTTP 400."""


class InternalError(AnalysisError):
    """Внутренняя ошибка, HTTP 500 и подклассы с 503/504."""

    code = "internal_error"


class InvalidRequestError(InputError):
    """Нет или неверные поля запроса."""

    code = "invalid_request"


class EmptyChecksError(InputError):
    """Список проверок пуст."""

    code = "empty_checks"


class UnknownChecksError(InputError):
    """Запрошены неизвестные проверки; состав передаётся в `args` для `details`."""

    code = "unknown_checks"

    def __init__(self, unknown: tuple[str, ...], available: tuple[str, ...]) -> None:
        super().__init__(unknown, available)


class FileTooLargeError(InputError):
    """Тело запроса больше допустимого размера."""

    code = "file_too_large"


class UnsupportedFormatError(InputError):
    """Формат не определён по сигнатуре."""

    code = "unsupported_format"


class DocumentUnreadableError(InputError):
    """Документ повреждён или не декодируется."""

    code = "document_unreadable"


class EncryptedPdfError(InputError):
    """PDF зашифрован."""

    code = "encrypted_pdf"


class TooManyPagesError(InputError):
    """Страниц PDF больше лимита."""

    code = "too_many_pages"


class TooManyPixelsError(InputError):
    """Изображение больше лимита пикселей по заголовку."""

    code = "too_many_pixels"


class OverloadedError(InternalError):
    """Лимит входа исчерпан, HTTP 503."""

    code = "overloaded"


class AnalysisTimeoutError(InternalError):
    """Анализ не уложился в таймаут, HTTP 504."""

    code = "analysis_timeout"


class WorkerCrashedError(InternalError):
    """Воркер завершился аварийно, HTTP 500."""

    code = "worker_crashed"
