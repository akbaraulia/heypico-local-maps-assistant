from typing import Annotated, Any

from pydantic import BaseModel, Field, StringConstraints, field_validator


class PlaceSearchParams(BaseModel):
    query: Annotated[str, StringConstraints(min_length=3, max_length=200)]

    @field_validator("query", mode="before")
    @classmethod
    def trim_query(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class Place(BaseModel):
    place_id: str
    name: str
    address: str | None
    rating: float | None
    user_rating_count: int | None
    open_now: bool | None
    primary_type: str | None
    price_level: str | None = None
    distance_meters: float | None = None
    lat: float
    lng: float
    google_maps_url: str
    directions_url: str
    current_opening_hours: dict[str, Any] | None = Field(
        default=None,
        exclude=True,
    )
    regular_opening_hours: dict[str, Any] | None = Field(
        default=None,
        exclude=True,
    )
    utc_offset_minutes: int | None = Field(default=None, exclude=True)


class PlaceSearchResponse(BaseModel):
    query: str
    count: int = Field(ge=0)
    places: list[Place]
