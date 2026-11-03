import asyncio
import multiprocessing
import os

from loguru import logger
from pebble import ProcessExpired, ProcessFuture, ProcessPool

from config.settings.analysis import AnalysisSettings
from core.errors import AnalysisTimeoutError, WorkerCrashedError
from core.models.analysis_types import AnalysisRequest, WorkerResult
from executor.admission_limiter import AdmissionLimiter
from executor.worker_tasks import init_worker, ping, run_analysis_task
from executor.worker_types import WorkerConfig

# Числовые библиотеки не должны плодить потоки внутри каждого воркера.
_THREAD_ENV_VARS: tuple[str, ...] = (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
)


class ProcessExecutor:
    """Исполнитель на пуле процессов pebble; реализует `AnalysisExecutor`.

    Слот лимита входа освобождается только колбэком завершения future pebble.
    Должен вызываться из цикла событий, в котором выполнен `start`.
    """

    def __init__(
        self,
        settings: AnalysisSettings,
        worker_config: WorkerConfig,
        limiter: AdmissionLimiter,
    ) -> None:
        self._settings = settings
        self._worker_config = worker_config
        self._limiter = limiter
        self._pool: ProcessPool | None = None

    async def start(self) -> None:
        """Создаёт пул и прогревает каждый воркер задачей `ping`.

        Raises:
            TimeoutError: воркеры не прогрелись за `warmup_timeout_s`.
            ProcessExpired: воркер упал при прогреве (например, в инициализаторе).
        """
        for name in _THREAD_ENV_VARS:
            os.environ[name] = "1"
        settings = self._settings
        pool = ProcessPool(
            max_workers=settings.pool_size,
            max_tasks=settings.max_tasks_per_worker,
            initializer=init_worker,
            initargs=(self._worker_config,),
            context=multiprocessing.get_context(settings.start_method),
        )
        self._pool = pool
        warmups = [
            asyncio.wrap_future(pool.schedule(ping, timeout=settings.warmup_timeout_s))
            for _ in range(settings.pool_size)
        ]
        try:
            await asyncio.gather(*warmups)
        except (TimeoutError, ProcessExpired):
            # Пул без прогрева не нужен: освобождаем процессы до проброса.
            logger.error("Worker pool warmup failed")
            await self._terminate(pool)
            raise
        logger.info("Worker pool started: {} processes", settings.pool_size)

    async def stop(self) -> None:
        """Закрывает пул, ждёт задачи до `task_timeout_s`, затем останавливает."""
        pool = self._pool
        if pool is None:
            return
        pool.close()
        try:
            await asyncio.to_thread(pool.join, self._settings.task_timeout_s)
        except TimeoutError:
            logger.warning("Worker pool did not stop in time, forcing stop")
            await self._terminate(pool)

    async def submit(self, request: AnalysisRequest) -> WorkerResult:
        """Выполняет запрос в процессе пула.

        Raises:
            OverloadedError: лимит входа исчерпан.
            AnalysisTimeoutError: задача превысила `task_timeout_s`.
            WorkerCrashedError: процесс воркера завершился аварийно.
            InputError: ошибка входных данных, проброшена из воркера как есть.
        """
        pool = self._require_pool()
        self._limiter.acquire()
        try:
            future: ProcessFuture = pool.schedule(
                run_analysis_task,
                args=(request, self._worker_config.check_modules),
                timeout=self._settings.task_timeout_s,
            )
        except BaseException:
            # Колбэк не будет навешен, поэтому слот возвращаем здесь.
            self._limiter.release()
            raise
        loop = asyncio.get_running_loop()
        # Колбэк вызывается из служебного потока pebble: возврат слота
        # передаём в цикл событий, где живёт лимитер. Навешивается до
        # wrap_future, чтобы слот освободился раньше ответа вызывающему.
        future.add_done_callback(
            lambda _: loop.call_soon_threadsafe(self._limiter.release)
        )
        try:
            # shield: отмена запроса не должна отменять задачу в пуле.
            return await asyncio.shield(asyncio.wrap_future(future))
        except TimeoutError as exc:
            raise AnalysisTimeoutError("analysis_timeout") from exc
        except ProcessExpired as exc:
            logger.warning(
                "Worker process expired: request_id={} exitcode={} pid={}",
                request.request_id,
                exc.exitcode,
                exc.pid,
            )
            raise WorkerCrashedError("worker_crashed") from exc

    def _require_pool(self) -> ProcessPool:
        """Пул после `start`; до него — ошибка использования."""
        if self._pool is None:
            raise RuntimeError("ProcessExecutor is not started")
        return self._pool

    @staticmethod
    async def _terminate(pool: ProcessPool) -> None:
        """Принудительно останавливает пул и дожидается его потоков."""
        pool.stop()
        await asyncio.to_thread(pool.join)
