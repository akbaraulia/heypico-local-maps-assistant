from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.core.config import Settings
from app.core.rate_limit import limiter
from app.main import create_app

MockHandler = Callable[[httpx.Request], httpx.Response]
ClientContext = Callable[[MockHandler], Iterator[TestClient]]


@pytest.fixture
def client_factory() -> ClientContext:
    @contextmanager
    def factory(handler: MockHandler) -> Iterator[TestClient]:
        settings = Settings(
            google_places_api_key=SecretStr("safe-test-key"),
            allowed_origins=["http://localhost:3000"],
            app_env="test",
            google_places_timeout_seconds=1,
            places_rate_limit="1000/minute",
            ollama_base_url="http://localhost:11434",
            ollama_model="qwen3:4b",
            ollama_timeout_seconds=1,
            chat_rate_limit="1000/minute",
            google_places_location_bias_radius_meters=5000,
        )
        transport = httpx.MockTransport(handler)
        limiter.reset()
        try:
            with TestClient(
                create_app(settings=settings, http_transport=transport)
            ) as client:
                yield client
        finally:
            limiter.reset()

    return factory


@pytest.fixture
def google_place() -> dict[str, Any]:
    return {
        "id": "place/with spaces",
        "displayName": {"text": "Warung Sunda"},
        "formattedAddress": "Jl. Pajajaran, Bogor",
        "location": {"latitude": -6.601, "longitude": 106.806},
        "rating": 4.5,
        "userRatingCount": 320,
        "currentOpeningHours": {"openNow": True},
        "primaryType": "restaurant",
        "googleMapsUri": "https://maps.google.com/?cid=123",
    }
