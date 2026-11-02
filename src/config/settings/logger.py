from pydantic import Field

from config.settings.base import BaseAppSettings


class LoggerSettings(BaseAppSettings):
    log_level: str = Field(default="DEBUG")
    log_to_console: bool = Field(default=True)
    max_frames: int = Field(default=10)
