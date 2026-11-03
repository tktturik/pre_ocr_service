from typing import Annotated

from fastapi import APIRouter, Depends, Request

from api.analysis.dependencies import (
    get_analysis_settings,
    get_body,
    get_check_names,
    get_requested_checks,
    get_service,
)
from api.analysis.schemas.analysis import AnalyzeResponse, to_analyze_response
from api.analysis.schemas.get import ChecksResponse
from config.settings.analysis import AnalysisSettings
from core.models.analysis_types import AnalysisLimits, AnalysisRequest
from services.analysis_service import AnalysisService

router = APIRouter()


@router.get("/checks")
async def list_checks(
    check_names: Annotated[tuple[str, ...], Depends(get_check_names)],
) -> ChecksResponse:
    """Возвращает имена доступных проверок."""
    return ChecksResponse(checks=list(check_names))


@router.post("/analyze")
async def analyze(
    request: Request,
    checks: Annotated[tuple[str, ...], Depends(get_requested_checks)],
    data: Annotated[bytes, Depends(get_body)],
    service: Annotated[AnalysisService, Depends(get_service)],
    settings: Annotated[AnalysisSettings, Depends(get_analysis_settings)],
) -> AnalyzeResponse:
    """Оценивает пригодность файла из тела запроса для OCR."""
    analysis_request = AnalysisRequest(
        request_id=request.state.request_id,
        data=data,
        checks=checks,
        limits=AnalysisLimits(
            max_raster_pixels=settings.max_raster_pixels,
            max_pdf_pages=settings.max_pdf_pages,
            pdf_fallback_dpi=settings.pdf_fallback_dpi,
        ),
    )
    result = await service.analyze(analysis_request)
    return to_analyze_response(result)
