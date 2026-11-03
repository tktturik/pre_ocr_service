from loguru import logger

from core.models.analysis_types import AnalysisRequest, DocumentResult
from core.scoring.document_scoring import score_document
from executor.process_executor import ProcessExecutor


class AnalysisService:
    """Сервис анализа: ставит запрос в исполнитель и оценивает документ."""

    def __init__(self, executor: ProcessExecutor) -> None:
        self._executor = executor

    async def analyze(self, request: AnalysisRequest) -> DocumentResult:
        """Выполняет запрос в воркере и возвращает итоговый результат документа.

        Raises:
            OverloadedError: лимит входа исчерпан.
            AnalysisTimeoutError: задача превысила `task_timeout_s`.
            WorkerCrashedError: процесс воркера завершился аварийно.
            InputError: ошибка входных данных, проброшена из воркера как есть.
        """
        worker_result = await self._executor.submit(request)
        verdict = score_document(worker_result.items)
        unsuitable = sum(
            1 for item in worker_result.items if item.verdict.suitable_for_ocr is False
        )
        logger.info(
            "Analysis finished: items={} unsuitable={} processing_time_ms={}",
            len(worker_result.items),
            unsuitable,
            worker_result.processing_time_ms,
        )
        return DocumentResult(
            verdict=verdict,
            items=worker_result.items,
            processing_time_ms=worker_result.processing_time_ms,
        )
