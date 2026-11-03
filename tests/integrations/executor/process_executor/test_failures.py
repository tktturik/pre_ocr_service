import pytest

from core.errors import AnalysisTimeoutError, WorkerCrashedError
from core.models.analysis_types import AnalysisRequest
from executor.process_executor import ProcessExecutor


async def test_submit_timeout_then_next_request_passes(
    executor: ProcessExecutor,
    sleep_request: AnalysisRequest,
    constant_request: AnalysisRequest,
) -> None:
    """Задача дольше таймаута даёт AnalysisTimeoutError, следующий запрос проходит."""
    with pytest.raises(AnalysisTimeoutError):
        await executor.submit(sleep_request)

    result = await executor.submit(constant_request)

    assert result.items[0].checks[0].name == "constant"


async def test_submit_worker_crash_then_next_request_passes(
    executor: ProcessExecutor,
    crash_request: AnalysisRequest,
    constant_request: AnalysisRequest,
) -> None:
    """Аварийный выход воркера даёт WorkerCrashedError, следующий запрос проходит."""
    with pytest.raises(WorkerCrashedError):
        await executor.submit(crash_request)

    result = await executor.submit(constant_request)

    assert result.items[0].checks[0].name == "constant"
