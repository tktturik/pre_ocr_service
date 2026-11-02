from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ScorePoints:
    """Опорные точки шкалы проверки: значение bad - 0, passed - 0.5, good — 1."""

    bad: float
    passed: float
    good: float

    def __post_init__(self) -> None:
        low, high = sorted((self.bad, self.good))
        if not low < self.passed < high:
            raise ValueError(
                f"passed должен лежать строго между bad и good: "
                f"bad={self.bad}, passed={self.passed}, good={self.good}"
            )


@dataclass(frozen=True, slots=True)
class CheckOutcome:
    """Результат одной проверки для одной единицы документа."""

    name: str
    passed: bool | None
    score: float | None
    # Сырое значение measure нужно только логу причин; в API не отдаётся (D24).
    value: float | None


@dataclass(frozen=True, slots=True)
class Verdict:
    """Вердикт по единице или по документу; None означает «не определено»."""

    suitable_for_ocr: bool | None
    quality_score: float | None


@dataclass(frozen=True, slots=True)
class ItemResult:
    """Результат одной единицы документа: страницы PDF или изображения."""

    index: int
    verdict: Verdict
    checks: tuple[CheckOutcome, ...]


@dataclass(frozen=True, slots=True)
class WorkerResult:
    """Результат выполнения запроса в воркере."""

    items: tuple[ItemResult, ...]
    processing_time_ms: int


@dataclass(frozen=True, slots=True)
class DocumentResult:
    """Итоговый результат анализа документа."""

    verdict: Verdict
    items: tuple[ItemResult, ...]
    processing_time_ms: int


@dataclass(frozen=True, slots=True)
class AnalysisLimits:
    """Лимиты обработки, которые api передаёт вместе с доменным запросом."""

    max_raster_pixels: int
    max_pdf_pages: int
    pdf_fallback_dpi: int


@dataclass(frozen=True, slots=True)
class AnalysisRequest:
    """Доменный запрос на анализ: тело файла, список проверок и лимиты."""

    # contextvar не переходит в spawn-процесс, поэтому идентификатор едет в модели.
    request_id: str
    data: bytes
    checks: tuple[str, ...]
    limits: AnalysisLimits
