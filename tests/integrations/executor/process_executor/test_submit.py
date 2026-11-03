import asyncio

import pytest

from core.errors import AnalysisTimeoutError, OverloadedError
from core.models.analysis_types import AnalysisRequest
from executor.analysis_worker import AnalysisWorker
from executor.process_executor import ProcessExecutor


async def test_submit_returns_same_items_as_direct_run(
    executor: ProcessExecutor,
    direct_worker: AnalysisWorker,
    constant_request: AnalysisRequest,
) -> None:
    """Результат через пул совпадает с прямым запуском воркера, кроме времени."""
    result = await executor.submit(constant_request)

    expected = direct_worker.run(constant_request)
    assert result.items == expected.items


async def test_submit_overloaded_when_full_and_slot_freed_after_error(
    executor: ProcessExecutor,
    sleep_request: AnalysisRequest,
    constant_request: AnalysisRequest,
) -> None:
    """При занятых N+M слотах submit сразу отказывает; слоты после ошибок свободны."""
    busy = [asyncio.create_task(executor.submit(sleep_request)) for _ in range(2)]
    # submit занимает слот до первого await, одной уступки циклу хватает.
    await asyncio.sleep(0)

    with pytest.raises(OverloadedError):
        await executor.submit(constant_request)

    errors = await asyncio.gather(*busy, return_exceptions=True)
    assert all(isinstance(error, AnalysisTimeoutError) for error in errors)
    result = await executor.submit(constant_request)
    assert result.items[0].checks[0].name == "constant"
