from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.analyzer.service import PythonAnalysisService
from app.schemas.analysis import (
    AnalysisRequest,
    AnalysisResponse,
)


router = APIRouter()

analysis_service = PythonAnalysisService()


@router.post("", response_model=AnalysisResponse)
def analyze_repository(
    request: AnalysisRequest,
) -> AnalysisResponse:
    repository_path = Path(
        request.repository_path
    )

    try:
        result = analysis_service.analyze_repository(
            repository_path
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    return AnalysisResponse.from_result(result)