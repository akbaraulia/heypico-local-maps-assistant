from typing import Any

import httpx
from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.core.config import Settings
from app.main import create_app
from app.services.google_places import (
    GOOGLE_PLACES_FIELD_MASK,
    GOOGLE_PLACES_TEXT_SEARCH_URL,
)


def test_valid_search_returns_normalized_places(
    client_factory,
    google_place: dict[str, Any],
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == GOOGLE_PLACES_TEXT_SEARCH_URL
        assert request.method == "POST"
        assert request.headers["X-Goog-FieldMask"] == GOOGLE_PLACES_FIELD_MASK
        assert request.headers["X-Goog-Api-Key"] == "safe-test-key"
        assert request.content == (
            b'{"textQuery":"restoran sunda di Bogor","maxResultCount":5}'
        )
        return httpx.Response(200, json={"places": [google_place]})

    with client_factory(handler) as client:
        response = client.get(
            "/api/places/search",
            params={"query": "  restoran sunda di Bogor  "},
        )

    assert response.status_code == 200
    assert response.json() == {
        "query": "restoran sunda di Bogor",
        "count": 1,
        "places": [
            {
                "place_id": "place/with spaces",
                "name": "Warung Sunda",
                "address": "Jl. Pajajaran, Bogor",
                "rating": 4.5,
                "user_rating_count": 320,
                "open_now": True,
                "primary_type": "restaurant",
                "price_level": None,
                "distance_meters": None,
                "lat": -6.601,
                "lng": 106.806,
                "google_maps_url": "https://maps.google.com/?cid=123",
                "directions_url": (
                    "https://www.google.com/maps/dir/"
                    "?api=1&destination=Warung+Sunda&destination_place_id=place%2Fwith+spaces"
                ),
            }
        ],
    }


def test_short_query_returns_422_without_google_call(client_factory) -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        raise AssertionError("Invalid input must not call Google.")

    with client_factory(handler) as client:
        response = client.get("/api/places/search", params={"query": "ab"})

    assert response.status_code == 422


def test_whitespace_only_query_returns_422_without_google_call(
    client_factory,
) -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        raise AssertionError("Invalid input must not call Google.")

    with client_factory(handler) as client:
        response = client.get("/api/places/search", params={"query": "    "})

    assert response.status_code == 422


def test_query_longer_than_200_characters_returns_422(client_factory) -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        raise AssertionError("Invalid input must not call Google.")

    with client_factory(handler) as client:
        response = client.get(
            "/api/places/search",
            params={"query": "x" * 201},
        )

    assert response.status_code == 422


def test_empty_google_result(client_factory) -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={})

    with client_factory(handler) as client:
        response = client.get(
            "/api/places/search",
            params={"query": "coffee Bogor"},
        )

    assert response.status_code == 200
    assert response.json() == {
        "query": "coffee Bogor",
        "count": 0,
        "places": [],
    }


def test_nullable_fields_and_maps_fallback_are_normalized(
    client_factory,
    google_place: dict[str, Any],
) -> None:
    nullable_place = {
        key: value
        for key, value in google_place.items()
        if key
        not in {
            "formattedAddress",
            "rating",
            "userRatingCount",
            "currentOpeningHours",
            "primaryType",
            "googleMapsUri",
        }
    }

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"places": [nullable_place]})

    with client_factory(handler) as client:
        response = client.get(
            "/api/places/search",
            params={"query": "warung Bogor"},
        )

    place = response.json()["places"][0]
    assert response.status_code == 200
    assert place["address"] is None
    assert place["rating"] is None
    assert place["user_rating_count"] is None
    assert place["open_now"] is None
    assert place["primary_type"] is None
    assert place["google_maps_url"].startswith(
        "https://www.google.com/maps/search/?"
    )
    assert "query_place_id=place%2Fwith+spaces" in place["google_maps_url"]


def test_place_without_coordinates_is_skipped(
    client_factory,
    google_place: dict[str, Any],
) -> None:
    malformed_place = {**google_place}
    malformed_place.pop("location")

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"places": [malformed_place, google_place]},
        )

    with client_factory(handler) as client:
        response = client.get(
            "/api/places/search",
            params={"query": "warung Bogor"},
        )

    assert response.status_code == 200
    assert response.json()["count"] == 1


def test_google_timeout_returns_504(client_factory) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("contains-safe-test-key", request=request)

    with client_factory(handler) as client:
        response = client.get(
            "/api/places/search",
            params={"query": "warung Bogor"},
        )

    assert response.status_code == 504
    assert response.json() == {
        "error": {
            "code": "google_places_timeout",
            "message": "Google Places request timed out.",
        }
    }
    assert "safe-test-key" not in response.text


def test_google_network_error_returns_503(client_factory) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("network failed", request=request)

    with client_factory(handler) as client:
        response = client.get(
            "/api/places/search",
            params={"query": "warung Bogor"},
        )

    assert response.status_code == 503
    assert response.json()["error"]["message"] == (
        "Google Places service is temporarily unavailable."
    )


def test_google_api_error_returns_safe_502(client_factory) -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            403,
            json={
                "error": {
                    "message": "raw provider error safe-test-key",
                    "internal": "must-not-leak",
                }
            },
        )

    with client_factory(handler) as client:
        response = client.get(
            "/api/places/search",
            params={"query": "warung Bogor"},
        )

    assert response.status_code == 502
    assert response.json() == {
        "error": {
            "code": "google_places_request_failed",
            "message": "Google Places request failed.",
        }
    }
    assert "safe-test-key" not in response.text
    assert "must-not-leak" not in response.text


def test_raw_google_response_is_not_exposed(
    client_factory,
    google_place: dict[str, Any],
) -> None:
    raw_place = {
        **google_place,
        "nationalPhoneNumber": "raw-only-field",
        "editorialSummary": {"text": "raw summary"},
    }

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"places": [raw_place], "nextPageToken": "raw-token"},
        )

    with client_factory(handler) as client:
        response = client.get(
            "/api/places/search",
            params={"query": "warung Bogor"},
        )

    assert response.status_code == 200
    assert "raw-only-field" not in response.text
    assert "raw summary" not in response.text
    assert "raw-token" not in response.text


def test_malformed_google_response_returns_502(client_factory) -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"places": "not-a-list"})

    with client_factory(handler) as client:
        response = client.get(
            "/api/places/search",
            params={"query": "warung Bogor"},
        )

    assert response.status_code == 502
    assert response.json()["error"]["code"] == "google_places_invalid_response"


def test_missing_api_key_returns_safe_configuration_error() -> None:
    settings = Settings(
        google_places_api_key=SecretStr(""),
        allowed_origins=["http://localhost:3000"],
        app_env="test",
        google_places_timeout_seconds=1,
        places_rate_limit="1000/minute",
    )

    def handler(_request: httpx.Request) -> httpx.Response:
        raise AssertionError("Missing API key must not call Google.")

    transport = httpx.MockTransport(handler)
    with TestClient(
        create_app(settings=settings, http_transport=transport)
    ) as client:
        response = client.get(
            "/api/places/search",
            params={"query": "warung Bogor"},
        )

    assert response.status_code == 500
    assert response.json() == {
        "error": {
            "code": "server_configuration_error",
            "message": "Server configuration error.",
        }
    }
    assert "key" not in response.text.lower()
