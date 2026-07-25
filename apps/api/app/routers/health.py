from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "heypico-local-maps-assistant-api",
        "version": "0.1.0",
    }
