from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import create_app
from config.settings.analysis import AnalysisSettings
from config.settings.logger import LoggerSettings


@pytest.fixture
def analysis_settings() -> AnalysisSettings:
    """Пул из одного процесса и проверки по умолчанию."""
    return AnalysisSettings(
        pool_size=1,
        queue_size=1,
        start_method="spawn",
    )


@pytest.fixture
def template_bytes() -> dict[str, bytes]:
    """Байты реальных файлов из tests/templates по имени файла."""
    templates = Path(__file__).parent.parent / "templates"
    return {path.name: path.read_bytes() for path in templates.iterdir()}


@pytest.fixture
def text_bytes() -> bytes:
    """Текстовое содержимое без сигнатуры поддерживаемого формата."""
    return b"plain text, not a document"


@pytest.fixture
def client(analysis_settings: AnalysisSettings) -> Iterator[TestClient]:
    """Клиент к приложению с реальным lifespan (пул spawn)."""
    app = create_app(analysis_settings, LoggerSettings())
    with TestClient(app) as test_client:
        yield test_client
