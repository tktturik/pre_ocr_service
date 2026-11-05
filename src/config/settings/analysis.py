import os
from typing import Literal, Self

from pydantic import Field, model_validator
from pydantic_settings import SettingsConfigDict

from config.settings.base import BaseAppSettings


class AnalysisSettings(BaseAppSettings):
    """Настройки анализа; читаются из переменных окружения с префиксом ANALYSIS_."""

    model_config = SettingsConfigDict(env_prefix="ANALYSIS_")

    max_file_bytes: int = Field(default=50 * 1024 * 1024)
    max_raster_pixels: int = Field(default=10000 * 10000)
    max_pdf_pages: int = Field(default=100)
    pdf_fallback_dpi: int = Field(default=300)
    pool_size: int = Field(default_factory=lambda: os.process_cpu_count() or 1)
    queue_size: int = Field(default=0)
    task_timeout_s: float = Field(default=60)
    warmup_timeout_s: float = Field(default=30)
    max_tasks_per_worker: int = Field(default=200)
    start_method: Literal["spawn", "forkserver"] = Field(default="spawn")
    check_modules: tuple[str, ...] = Field(
        default=(
            "core.checks.resolution_check",
            "core.checks.sharpness_check",
            "core.checks.tonal_range_check",
            "core.checks.illumination_check",
        )
    )

    @model_validator(mode="after")
    def _queue_size_defaults_to_pool_size(self) -> Self:
        if "queue_size" not in self.model_fields_set:
            self.queue_size = self.pool_size
        return self
