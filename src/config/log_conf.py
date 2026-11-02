import logging
import sys
import traceback
from pathlib import Path
from types import TracebackType
from typing import TYPE_CHECKING

from loguru import logger

from config.log_context import page_var, request_id_var
from config.settings.logger import LoggerSettings

if TYPE_CHECKING:
    from loguru import Record

# Каталоги окружения и установленных пакетов: кадры из них не считаются кадрами проекта.
_LIBRARY_DIRS = frozenset({"venv", ".venv", "site-packages"})

_CHAIN_SEPARATOR = "--- caused by / during handling of the above ---"


def _is_project_frame(frame: traceback.FrameSummary, project_root: Path) -> bool:
    """Кадр лежит под корнем проекта и не в каталоге окружения."""
    try:
        rel_path = Path(frame.filename).relative_to(project_root)
    except ValueError:
        return False
    return not _LIBRARY_DIRS.intersection(rel_path.parts)


def _format_frame(frame: traceback.FrameSummary, index: int, project_root: Path) -> str:
    try:
        shown = Path(frame.filename).relative_to(project_root)
    except ValueError:
        shown = Path(frame.filename)
    line = frame.line.strip() if frame.line else ""
    return f'{"└" + "──" * index}> File "{shown}", line {frame.lineno}, in {frame.name}: \t[{line}]'


def _format_single(
    exc: BaseException, project_root: Path, max_frames: int
) -> str:
    """Форматирует одно звено цепочки: кадры проекта (последние max_frames) и строку исключения."""
    frames = traceback.extract_tb(exc.__traceback__)
    selected = [f for f in frames if _is_project_frame(f, project_root)]
    if not selected and frames:
        # Своих кадров нет: место падения в библиотеке не теряем.
        selected = [frames[-1]]
    selected = selected[-max_frames:]
    exc_line = "".join(traceback.format_exception_only(type(exc), exc)).rstrip()
    if not selected:
        return exc_line
    lines = [_format_frame(f, i, project_root) for i, f in enumerate(selected)]
    return "\n".join(lines) + f"\n  {exc_line}"


def _exception_chain(exc: BaseException) -> list[BaseException]:
    """Цепочка от первопричины к внешнему исключению."""
    chain: list[BaseException] = []
    seen: set[int] = set()
    current: BaseException | None = exc
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        chain.append(current)
        if current.__cause__ is not None:
            current = current.__cause__
        elif not current.__suppress_context__:
            current = current.__context__
        else:
            current = None
    chain.reverse()
    return chain


def format_exception_with_filtered_traceback(
    exc_type: type[BaseException],
    exc_value: BaseException,
    exc_traceback: TracebackType | None,
    project_root: Path,
    max_frames: int,
) -> str:
    """Форматирует исключение с цепочкой `__cause__`/`__context__` и стеком, отфильтрованным по кадрам проекта.

    Звенья идут от первопричины к внешнему исключению. Если у звена нет кадров проекта,
    печатается последний кадр библиотеки. Выводится не более `max_frames` последних кадров на звено.
    """
    if exc_value.__traceback__ is not exc_traceback:
        exc_value = exc_value.with_traceback(exc_traceback)
    chain = _exception_chain(exc_value)
    return f"\n{_CHAIN_SEPARATOR}\n".join(
        _format_single(link, project_root, max_frames) for link in chain
    )


def add_log_context(record: "Record") -> None:
    """Patcher loguru: кладёт в `extra` request_id и page из contextvar."""
    record["extra"]["request_id"] = request_id_var.get()
    record["extra"]["page"] = page_var.get()


class InterceptHandler(logging.Handler):
    """Перенаправляет записи стандартного logging в loguru с фильтрованным стеком исключений."""

    def __init__(self, project_root: Path, max_frames: int) -> None:
        super().__init__()
        self._project_root = project_root
        self._max_frames = max_frames

    def emit(self, record: logging.LogRecord) -> None:
        """Передаёт запись в loguru; не завершает процесс ни на каком уровне."""
        try:
            level: str | int = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame = sys._getframe(1)
        depth = 1
        # Пропускаем кадры logging и loguru, чтобы место вызова было настоящим.
        while frame and (
            frame.f_code.co_filename == logging.__file__
            or "loguru" in frame.f_code.co_filename
        ):
            frame = frame.f_back
            depth += 1

        message = record.getMessage()
        if record.exc_info and record.exc_info[1] is not None:
            exc_type, exc_value, exc_traceback = record.exc_info
            formatted = format_exception_with_filtered_traceback(
                exc_type,
                exc_value,
                exc_traceback,
                self._project_root,
                self._max_frames,
            )
            message = f"{message}\n{formatted}"

        logger.opt(depth=depth).log(level, message)


def setup_logging(cfg: LoggerSettings, enqueue: bool, project_root: Path) -> None:
    """Настраивает loguru и перехват стандартного logging.

    Вызывается в API (`enqueue=True`) и в инициализаторе воркера (`enqueue=False`).
    """
    log_format = (
        "[<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green>] "
        "<level>{level: >8}</level> - request_id={extra[request_id]} "
        "<level><white>{message}</white></level> "
        "({file}:{line})"
    )

    logging.root.handlers = []
    logging.root.setLevel(logging.NOTSET)
    logging.basicConfig(
        handlers=[InterceptHandler(project_root, cfg.max_frames)], level=0
    )

    logger.remove()
    logger.configure(patcher=add_log_context)

    if cfg.log_to_console:
        logger.add(
            sys.stdout,
            format=log_format,
            level=cfg.log_level,
            backtrace=False,
            diagnose=False,
            enqueue=enqueue,
            colorize=True,
        )
