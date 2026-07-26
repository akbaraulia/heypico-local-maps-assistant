from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import Settings, get_settings
from app.core.exceptions import register_exception_handlers
from app.core.rate_limit import limiter
from app.routers.chat import router as chat_router
from app.routers.health import router as health_router
from app.routers.places import router as places_router


def create_app(
    *,
    settings: Settings | None = None,
    http_transport: httpx.AsyncBaseTransport | None = None,
) -> FastAPI:
    app_settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        async with httpx.AsyncClient(
            timeout=app_settings.google_places_timeout_seconds,
            transport=http_transport,
        ) as client:
            app.state.http_client = client
            yield

    application = FastAPI(
        title="HeyPico Local Maps Assistant API",
        version="0.1.0",
        description=(
            "Backend API for local place discovery using Google Places API "
            "and local Ollama orchestration."
        ),
        lifespan=lifespan,
    )
    application.state.settings = app_settings
    application.state.limiter = limiter
    application.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Accept", "Content-Type"],
    )
    register_exception_handlers(application)
    application.include_router(health_router)
    application.include_router(places_router)
    application.include_router(chat_router)
    return application


app = create_app()
