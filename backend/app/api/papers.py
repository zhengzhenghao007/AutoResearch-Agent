from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from backend.app.schemas.paper import (
    PaperSearchRequest,
    PaperSearchResponse,
)
from backend.app.services.research_service import (
    ResearchService,
)


router = APIRouter(
    prefix="/api/papers",
    tags=["papers"],
)

research_service = ResearchService()


@router.post(
    "/search",
    response_model=PaperSearchResponse,
    status_code=status.HTTP_200_OK,
)
def search_papers(
    request: PaperSearchRequest,
) -> PaperSearchResponse:
    """
    Search arXiv papers from a research topic or query.
    """
    try:
        result = research_service.search_papers(
            topic=request.topic,
            max_results=request.max_results,
        )

        return PaperSearchResponse(
            **result
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    except Exception as error:
        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "Paper search failed: "
                f"{error}"
            ),
        ) from error