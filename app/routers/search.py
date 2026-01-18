"""
Search API endpoints
"""
from fastapi import APIRouter, HTTPException
from app.schemas.search import (
    SearchRequest,
    InitialSearchResponse,
    ShopDetailRequest,
    ShopDetailSearchResponse
)
from app.services.search_service import SearchService
from app.logger import logger

router = APIRouter(prefix="/api", tags=["search"])

# Initialize search service
search_service = SearchService()


@router.post("/search", response_model=InitialSearchResponse)
async def initial_search(request: SearchRequest):
    """
    Step 1-3: Initial Grounding Search and shop name extraction

    Now uses real Google AI integration (Stage 3)
    """
    logger.info(f"[POST /api/search] Received request: {request.input_text}")

    try:
        # Use real search service with AI integration
        response = search_service.initial_search(request.input_text)
        logger.info(f"[POST /api/search] Returning {len(response.shop_list.shops)} shops")
        return response

    except Exception as e:
        logger.error(f"[POST /api/search] Error: {type(e).__name__}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )


@router.post("/search/detail", response_model=ShopDetailSearchResponse)
async def detail_search(request: ShopDetailRequest):
    """
    Step 4-5: Individual shop detail search and match judgement

    Now uses real Google AI integration (Stage 5)
    """
    logger.info(f"[POST /api/search/detail] Received request for {len(request.shop_names)} shops")

    try:
        # Use real search service with AI integration
        response = search_service.detail_search(request.input_text, request.shop_names)
        logger.info(f"[POST /api/search/detail] Returning {len(response.summaries)} summaries")
        return response

    except Exception as e:
        logger.error(f"[POST /api/search/detail] Error: {type(e).__name__}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Detail search failed: {str(e)}"
        )
