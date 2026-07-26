from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.core.rate_limit import get_chat_rate_limit, limiter
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.error import ErrorResponse
from app.services.chat import ChatService, get_chat_service

router = APIRouter(prefix="/api", tags=["chat"])


@router.post(
    "/chat",
    response_model=ChatResponse,
    response_model_exclude_unset=True,
    responses={
        429: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
        502: {"description": "Upstream service returned an invalid response."},
        503: {"description": "A required upstream service is unavailable."},
        504: {"description": "A required upstream service timed out."},
    },
)
@limiter.limit(get_chat_rate_limit)
async def chat(
    request: Request,
    payload: ChatRequest,
    service: Annotated[ChatService, Depends(get_chat_service)],
) -> ChatResponse:
    del request
    return await service.chat(payload)
