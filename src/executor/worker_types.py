from dataclasses import dataclass
from pathlib import Path

from config.settings.logger import LoggerSettings


@dataclass(frozen=True, slots=True)
class WorkerConfig:
    """Параметры инициализатора воркера; пересекает границу процесса целиком."""

    check_modules: tuple[str, ...]
    logger: LoggerSettings
    project_root: Path
