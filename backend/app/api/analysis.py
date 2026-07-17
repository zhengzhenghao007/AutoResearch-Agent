from __future__ import annotations

from fastapi import (
    APIRouter,
    HTTPException,
    status,
)

from backend.app.schemas.analysis import (
    PaperAnalysisRequest,
    PaperAnalysisResponse,
)
from backend.app.services.analysis_service import (
    AnalysisService,
)


router = APIRouter(
    prefix="/api/papers",
    tags=["paper analysis"],
)

analysis_service = AnalysisService()


@router.post(
    "/analyze",
    response_model=PaperAnalysisResponse,
    status_code=status.HTTP_200_OK,
)
def analyze_paper(
    request: PaperAnalysisRequest,
) -> PaperAnalysisResponse:
    """
    Download and analyze one academic paper.
    """
    try:
        result = analysis_service.analyze_paper(
            request
        )

        return PaperAnalysisResponse(
            **result
        )

    except ValueError as error:
        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=str(error),
        ) from error

    except IndexError as error:
        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=str(error),
        ) from error

    except FileNotFoundError as error:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=str(error),
        ) from error

    except Exception as error:
        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "Paper analysis failed: "
                f"{error}"
            ),
        ) from error