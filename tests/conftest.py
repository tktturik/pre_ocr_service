import io
from pathlib import Path

import pytest
from dotenv import load_dotenv
from PIL import Image


def pytest_configure(config):
    """Загружает .env.test ДО всех импортов."""
    env_path = Path(__file__).parent / ".env.test"
    load_dotenv(env_path, override=True)


@pytest.fixture
def png_bytes() -> bytes:
    """Малый серый PNG."""
    buffer = io.BytesIO()
    Image.new("L", (16, 16), color=128).save(buffer, format="PNG")
    return buffer.getvalue()
