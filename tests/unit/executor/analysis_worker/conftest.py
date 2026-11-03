import numpy as np
import pytest

from core.checks.base_check import Check, build_check_registry
from core.loaders.image_loader import ImageLoader
from core.models.analysis_types import AnalysisLimits, AnalysisRequest
from core.models.raster_types import Raster, UnitError
from core.registry import Registry
from executor.analysis_worker import AnalysisWorker
from tests.fakes.fake_loader import FakeLoader


@pytest.fixture
def limits() -> AnalysisLimits:
    """Лимиты с запасом для малых растров."""
    return AnalysisLimits(
        max_raster_pixels=1_000_000, max_pdf_pages=10, pdf_fallback_dpi=100
    )


@pytest.fixture
def constant_registry() -> Registry[Check]:
    """Реестр с одной проверкой constant."""
    return build_check_registry(["tests.fakes.constant_check"])


@pytest.fixture
def mixed_registry() -> Registry[Check]:
    """Реестр с проверками raising и constant."""
    return build_check_registry(
        ["tests.fakes.raising_check", "tests.fakes.constant_check"]
    )


@pytest.fixture
def png_request(png_bytes: bytes, limits: AnalysisLimits) -> AnalysisRequest:
    """Запрос с PNG и проверкой constant."""
    return AnalysisRequest("rid", png_bytes, ("constant",), limits)


@pytest.fixture
def mixed_request(png_bytes: bytes, limits: AnalysisLimits) -> AnalysisRequest:
    """Запрос с PNG и проверками raising, constant."""
    return AnalysisRequest("rid", png_bytes, ("raising", "constant"), limits)


@pytest.fixture
def fake_request(limits: AnalysisLimits) -> AnalysisRequest:
    """Запрос для фиктивного загрузчика; содержимое не важно."""
    return AnalysisRequest("rid", b"fake", ("constant",), limits)


@pytest.fixture
def png_worker(constant_registry: Registry[Check]) -> AnalysisWorker:
    """Воркер с реальным загрузчиком изображений и проверкой constant."""
    return AnalysisWorker(constant_registry, [ImageLoader()])


@pytest.fixture
def mixed_worker(mixed_registry: Registry[Check]) -> AnalysisWorker:
    """Воркер с реальным загрузчиком изображений, проверки raising и constant."""
    return AnalysisWorker(mixed_registry, [ImageLoader()])


@pytest.fixture
def broken_unit_worker(constant_registry: Registry[Check]) -> AnalysisWorker:
    """Воркер, чей загрузчик отдаёт Raster, UnitError, Raster."""
    pixels = np.zeros((8, 8), dtype=np.uint8)
    loader = FakeLoader([Raster(1, pixels), UnitError(2, "broken"), Raster(3, pixels)])
    return AnalysisWorker(constant_registry, [loader])
