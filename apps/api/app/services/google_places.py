import logging
import math
from typing import Any
from urllib.parse import urlencode

import httpx
from fastapi import Request

from app.core.config import Settings
from app.core.exceptions import (
    GooglePlacesMalformedResponseError,
    GooglePlacesRequestError,
    GooglePlacesTimeoutError,
    GooglePlacesUnavailableError,
    ServerConfigurationError,
)
from app.schemas.place import Place

logger = logging.getLogger(__name__)

GOOGLE_PLACES_TEXT_SEARCH_URL = (
    "https://places.googleapis.com/v1/places:searchText"
)
GOOGLE_PLACES_FIELD_MASK = ",".join(
    (
        "places.id",
        "places.displayName",
        "places.formattedAddress",
        "places.location",
        "places.rating",
        "places.userRatingCount",
        "places.currentOpeningHours.openNow",
        "places.primaryType",
        "places.googleMapsUri",
    )
)


class GooglePlacesService:
    def __init__(
        self,
        settings: Settings,
        client: httpx.AsyncClient,
    ) -> None:
        self._settings = settings
        self._client = client

    async def search_text(self, query: str) -> list[Place]:
        api_key = self._api_key()
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": GOOGLE_PLACES_FIELD_MASK,
        }
        payload = {"textQuery": query, "maxResultCount": 5}

        try:
            response = await self._client.post(
                GOOGLE_PLACES_TEXT_SEARCH_URL,
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            logger.warning("google_places_timeout")
            raise GooglePlacesTimeoutError() from exc
        except httpx.HTTPStatusError as exc:
            logger.warning(
                "google_places_http_error status_code=%s",
                exc.response.status_code,
            )
            raise GooglePlacesRequestError() from exc
        except httpx.RequestError as exc:
            logger.warning("google_places_network_error")
            raise GooglePlacesUnavailableError() from exc

        try:
            data = response.json()
        except ValueError as exc:
            logger.warning("google_places_invalid_json")
            raise GooglePlacesMalformedResponseError() from exc

        if not isinstance(data, dict):
            raise GooglePlacesMalformedResponseError()

        raw_places = data.get("places", [])
        if not isinstance(raw_places, list):
            raise GooglePlacesMalformedResponseError()

        normalized: list[Place] = []
        for raw_place in raw_places[:5]:
            place = self._normalize_place(raw_place)
            if place is not None:
                normalized.append(place)
        return normalized

    def _api_key(self) -> str:
        secret = self._settings.google_places_api_key
        api_key = secret.get_secret_value().strip() if secret else ""
        if not api_key:
            logger.error("google_places_configuration_missing")
            raise ServerConfigurationError()
        return api_key

    @staticmethod
    def _normalize_place(raw_place: Any) -> Place | None:
        if not isinstance(raw_place, dict):
            return None

        place_id = _clean_string(raw_place.get("id"))
        display_name = raw_place.get("displayName")
        name = (
            _clean_string(display_name.get("text"))
            if isinstance(display_name, dict)
            else None
        )
        location = raw_place.get("location")
        if not place_id or not name or not isinstance(location, dict):
            return None

        lat = _finite_number(location.get("latitude"))
        lng = _finite_number(location.get("longitude"))
        if lat is None or lng is None:
            return None

        official_maps_url = _clean_string(raw_place.get("googleMapsUri"))
        google_maps_url = official_maps_url or _maps_search_url(place_id, name)

        opening_hours = raw_place.get("currentOpeningHours")
        open_now = (
            _optional_bool(opening_hours.get("openNow"))
            if isinstance(opening_hours, dict)
            else None
        )

        return Place(
            place_id=place_id,
            name=name,
            address=_clean_string(raw_place.get("formattedAddress")),
            rating=_finite_number(raw_place.get("rating")),
            user_rating_count=_optional_int(raw_place.get("userRatingCount")),
            open_now=open_now,
            primary_type=_clean_string(raw_place.get("primaryType")),
            lat=lat,
            lng=lng,
            google_maps_url=google_maps_url,
            directions_url=_directions_url(place_id),
        )


def get_google_places_service(request: Request) -> GooglePlacesService:
    return GooglePlacesService(
        settings=request.app.state.settings,
        client=request.app.state.http_client,
    )


def _clean_string(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    cleaned = value.strip()
    return cleaned or None


def _finite_number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    return number if math.isfinite(number) else None


def _optional_int(value: Any) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _optional_bool(value: Any) -> bool | None:
    return value if isinstance(value, bool) else None


def _directions_url(place_id: str) -> str:
    query = urlencode({"api": "1", "destination_place_id": place_id})
    return f"https://www.google.com/maps/dir/?{query}"


def _maps_search_url(place_id: str, name: str) -> str:
    query = urlencode(
        {"api": "1", "query": name, "query_place_id": place_id}
    )
    return f"https://www.google.com/maps/search/?{query}"
