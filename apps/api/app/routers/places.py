from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request

from app.core.rate_limit import get_places_rate_limit, limiter
from app.schemas.error import ErrorResponse
from app.schemas.place import PlaceSearchParams, PlaceSearchResponse
from app.services.google_places import GooglePlacesService, get_google_places_service

router = APIRouter(prefix="/api/places", tags=["places"])


@router.get(
    "/search",
    response_model=PlaceSearchResponse,
    responses={
        429: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
        502: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
        504: {"model": ErrorResponse},
    },
)
@limiter.limit(get_places_rate_limit)
async def search_places(
    request: Request,
    params: Annotated[PlaceSearchParams, Query()],
    service: Annotated[GooglePlacesService, Depends(get_google_places_service)],
) -> PlaceSearchResponse:
    del request
    places = await service.search_text(params.query)
    return PlaceSearchResponse(
        query=params.query,
        count=len(places),
        places=places,
    )
