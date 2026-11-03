from pydantic import BaseModel

from core.models.analysis_types import DocumentResult


class CheckSchema(BaseModel):
    """Результат одной проверки; `null` означает «не определено»."""

    passed: bool | None
    score: float | None


class ItemSchema(BaseModel):
    """Результат единицы документа: страницы PDF или изображения."""

    index: int
    suitable_for_ocr: bool | None
    quality_score: float | None
    checks: dict[str, CheckSchema]


class AnalyzeResponse(BaseModel):
    """Тело ответа `POST /analyze`."""

    suitable_for_ocr: bool | None
    quality_score: float | None
    processing_time_ms: int
    items: list[ItemSchema]


def to_analyze_response(result: DocumentResult) -> AnalyzeResponse:
    """Переводит итог анализа в ответ; `checks` единиц идут в порядке запроса."""
    items = [
        ItemSchema(
            index=item.index,
            suitable_for_ocr=item.verdict.suitable_for_ocr,
            quality_score=item.verdict.quality_score,
            checks={
                outcome.name: CheckSchema(passed=outcome.passed, score=outcome.score)
                for outcome in item.checks
            },
        )
        for item in result.items
    ]
    return AnalyzeResponse(
        suitable_for_ocr=result.verdict.suitable_for_ocr,
        quality_score=result.verdict.quality_score,
        processing_time_ms=result.processing_time_ms,
        items=items,
    )
