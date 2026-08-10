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
    try:
        if request.repository_url:
            result = (
                analysis_service.analyze_repository_url(
                    request.repository_url
                )
            )

        elif request.repository_path:
            result = (
                analysis_service.analyze_repository(
                    Path(request.repository_path)
                )
            )

        else:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Provide either repository_path "
                    "or repository_url."
                ),
            )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    return AnalysisResponse.from_result(
        result
    )