import logging
import math
from typing import Any
from urllib.parse import quote, urlencode

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
        "places.currentOpeningHours.periods",
        "places.currentOpeningHours.nextCloseTime",
        "places.regularOpeningHours.periods",
        "places.utcOffsetMinutes",
        "places.primaryType",
        "places.priceLevel",
        "places.googleMapsUri",
    )
)
GOOGLE_PLACE_DETAILS_FIELD_MASK = ",".join(
    (
        "id",
        "displayName",
        "formattedAddress",
        "location",
        "rating",
        "userRatingCount",
        "currentOpeningHours",
        "regularOpeningHours",
        "utcOffsetMinutes",
        "primaryType",
        "priceLevel",
        "googleMapsUri",
    )
)
GOOGLE_PRICE_LEVELS = {
    "PRICE_LEVEL_FREE",
    "PRICE_LEVEL_INEXPENSIVE",
    "PRICE_LEVEL_MODERATE",
    "PRICE_LEVEL_EXPENSIVE",
    "PRICE_LEVEL_VERY_EXPENSIVE",
}
GOOGLE_PRICE_FILTER_LEVELS = {
    "PRICE_LEVEL_INEXPENSIVE",
    "PRICE_LEVEL_MODERATE",
    "PRICE_LEVEL_EXPENSIVE",
    "PRICE_LEVEL_VERY_EXPENSIVE",
}


class GooglePlacesService:
    def __init__(
        self,
        settings: Settings,
        client: httpx.AsyncClient,
    ) -> None:
        self._settings = settings
        self._client = client

    async def search_text(
        self,
        query: str,
        *,
        user_lat: float | None = None,
        user_lng: float | None = None,
        price_levels: list[str] | None = None,
        open_now: bool = False,
        max_results: int = 5,
    ) -> list[Place]:
        result_count = max(1, min(20, max_results))
        payload: dict[str, Any] = {
            "textQuery": query,
            "maxResultCount": result_count,
        }
        if price_levels:
            if not set(price_levels) <= GOOGLE_PRICE_FILTER_LEVELS:
                raise ValueError("Unsupported Google Places price filter.")
            payload["priceLevels"] = price_levels
        if open_now:
            payload["openNow"] = True
        if user_lat is not None and user_lng is not None:
            payload["locationBias"] = {
                "circle": {
                    "center": {
                        "latitude": user_lat,
                        "longitude": user_lng,
                    },
                    "radius": (
                        self._settings.google_places_location_bias_radius_meters
                    ),
                }
            }

        try:
            data = await self._post_search(payload)
        except GooglePlacesRequestError as exc:
            if (
                exc.upstream_status_code != 400
                or "priceLevels" not in payload
            ):
                raise
            fallback_payload = dict(payload)
            fallback_payload.pop("priceLevels")
            logger.warning(
                "google_places_optional_filter_fallback "
                "status_code=400 operation=text_search fields=%s",
                sorted(fallback_payload),
            )
            data = await self._post_search(fallback_payload)

        raw_places = data.get("places", [])
        if not isinstance(raw_places, list):
            raise GooglePlacesMalformedResponseError()

        normalized: list[Place] = []
        for raw_place in raw_places[:result_count]:
            place = self._normalize_place(raw_place)
            if place is not None:
                normalized.append(place)
        return normalized

    async def get_place_details(self, place_id: str) -> Place:
        api_key = self._api_key()
        url = (
            "https://places.googleapis.com/v1/places/"
            f"{quote(place_id, safe='')}"
        )
        headers = {
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": GOOGLE_PLACE_DETAILS_FIELD_MASK,
        }
        data = await self._request_json("GET", url, headers=headers)
        place = self._normalize_place(data)
        if place is None:
            raise GooglePlacesMalformedResponseError()
        return place

    async def _post_search(self, payload: dict[str, Any]) -> dict[str, Any]:
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self._api_key(),
            "X-Goog-FieldMask": GOOGLE_PLACES_FIELD_MASK,
        }
        return await self._request_json(
            "POST",
            GOOGLE_PLACES_TEXT_SEARCH_URL,
            headers=headers,
            json=payload,
        )

    async def _request_json(
        self,
        method: str,
        url: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        try:
            response = await self._client.request(method, url, **kwargs)
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            logger.warning("google_places_timeout")
            raise GooglePlacesTimeoutError() from exc
        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code
            logger.warning(
                "google_places_http_error status_code=%s",
                status_code,
            )
            raise GooglePlacesRequestError(status_code=status_code) from exc
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
        return data

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

        current_hours = _opening_hours(raw_place.get("currentOpeningHours"))
        regular_hours = _opening_hours(raw_place.get("regularOpeningHours"))
        open_now = (
            _optional_bool(current_hours.get("openNow"))
            if current_hours
            else None
        )
        official_maps_url = _clean_string(raw_place.get("googleMapsUri"))

        return Place(
            place_id=place_id,
            name=name,
            address=_clean_string(raw_place.get("formattedAddress")),
            rating=_finite_number(raw_place.get("rating")),
            user_rating_count=_optional_int(raw_place.get("userRatingCount")),
            open_now=open_now,
            primary_type=_clean_string(raw_place.get("primaryType")),
            price_level=_price_level(raw_place.get("priceLevel")),
            lat=lat,
            lng=lng,
            google_maps_url=(
                official_maps_url or _maps_search_url(place_id, name)
            ),
            directions_url=_directions_url(place_id, name, lat, lng),
            current_opening_hours=current_hours,
            regular_opening_hours=regular_hours,
            utc_offset_minutes=_optional_int(
                raw_place.get("utcOffsetMinutes")
            ),
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


def _opening_hours(value: Any) -> dict[str, Any] | None:
    return value if isinstance(value, dict) else None


def _price_level(value: Any) -> str | None:
    return value if isinstance(value, str) and value in GOOGLE_PRICE_LEVELS else None


def _directions_url(
    place_id: str,
    name: str | None = None,
    lat: float | None = None,
    lng: float | None = None,
) -> str:
    destination = name or (
        f"{lat},{lng}" if lat is not None and lng is not None else place_id
    )
    query = urlencode(
        {"api": "1", "destination": destination, "destination_place_id": place_id}
    )
    return f"https://www.google.com/maps/dir/?{query}"


def _maps_search_url(place_id: str, name: str) -> str:
    query = urlencode(
        {"api": "1", "query": name, "query_place_id": place_id}
    )
    return f"https://www.google.com/maps/search/?{query}"
