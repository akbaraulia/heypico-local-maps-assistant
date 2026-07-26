from enum import Enum
from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

from app.schemas.place import Place

ChatIntent = Literal[
    "place_search",
    "place_refinement",
    "place_detail",
    "general",
    "unsupported",
]
ChatLanguage = Literal["id", "en"]
TrimmedContent = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=1000),
]
ContextText = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=500),
]
PlaceId = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=300),
]


class ParserAction(str, Enum):
    SEARCH_PLACES = "search_places"
    REFINE_SEARCH = "refine_search"
    ANSWER_FROM_CONTEXT = "answer_from_context"
    SELECT_PLACE = "select_place"
    GET_PLACE_DETAILS = "get_place_details"
    ASK_CLARIFICATION = "ask_clarification"
    ACKNOWLEDGE = "acknowledge"
    GENERAL = "general"
    UNSUPPORTED = "unsupported"


class RequestedDetail(str, Enum):
    PRICE_RANGE = "price_range"
    CLOSING_TIME = "closing_time"
    OPENING_HOURS = "opening_hours"
    ADDRESS = "address"
    RATING = "rating"
    DIRECTIONS = "directions"
    NONE = "none"


class ChatHistoryMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: TrimmedContent

    model_config = ConfigDict(extra="forbid")


class PlaceReference(BaseModel):
    place_id: PlaceId
    name: ContextText
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    price_level: str | None = None
    rating: float | None = Field(default=None, ge=0, le=5)
    user_rating_count: int | None = Field(default=None, ge=0)
    open_now: bool | None = None

    model_config = ConfigDict(extra="forbid")


class SearchContext(BaseModel):
    last_intent: ChatIntent | None = None
    last_search_terms: ContextText | None = None
    last_location: ContextText | None = None
    last_search_query: ContextText | None = None
    last_place_ids: list[PlaceId] = Field(default_factory=list, max_length=10)
    last_places: list[PlaceReference] = Field(default_factory=list, max_length=10)
    reference_lat: float | None = Field(default=None, ge=-90, le=90)
    reference_lng: float | None = Field(default=None, ge=-180, le=180)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_reference_pair(self) -> "SearchContext":
        if (self.reference_lat is None) != (self.reference_lng is None):
            raise ValueError(
                "reference_lat and reference_lng must be supplied together."
            )
        return self


class ChatRequest(BaseModel):
    message: Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=2, max_length=500),
    ]
    language: ChatLanguage | None = None
    user_lat: float | None = Field(default=None, ge=-90, le=90)
    user_lng: float | None = Field(default=None, ge=-180, le=180)
    history: list[ChatHistoryMessage] = Field(default_factory=list, max_length=10)
    context: SearchContext | None = None

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "message": "Cari cafe di Kebun Raya Bogor",
                    "language": "id",
                },
                {
                    "message": "yang lebih murah?",
                    "language": "id",
                    "history": [
                        {
                            "role": "user",
                            "content": "Cari bakso di Gadog, Kabupaten Bogor",
                        }
                    ],
                    "context": {
                        "last_intent": "place_search",
                        "last_search_terms": "bakso",
                        "last_location": "Gadog, Kabupaten Bogor",
                        "last_search_query": (
                            "bakso di Gadog, Kabupaten Bogor"
                        ),
                        "last_place_ids": [],
                        "last_places": [],
                    },
                },
            ]
        },
    )

    @model_validator(mode="after")
    def validate_coordinate_pair(self) -> "ChatRequest":
        if (self.user_lat is None) != (self.user_lng is None):
            raise ValueError("user_lat and user_lng must be supplied together.")
        return self


class RefinementFlags(BaseModel):
    cheaper: bool = False
    higher_rated: bool = False
    open_now: bool = False
    open_24_hours: bool = False
    nearest: bool = False
    alternatives: bool = False
    family_friendly: bool = False

    model_config = ConfigDict(extra="forbid")

    def any_enabled(self) -> bool:
        return any(self.model_dump().values())


class IntentAnalysis(BaseModel):
    action: ParserAction
    search_terms: str | None
    location: str | None
    language: ChatLanguage
    response_style: Literal["casual", "neutral", "formal"] = "neutral"
    requested_result_count: int | None
    place_reference: str | None
    selected_result_index: int | None = Field(default=None, ge=1, le=10)
    requested_detail: RequestedDetail
    refinements: RefinementFlags
    requires_clarification: bool
    clarification_reason: str | None = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("search_terms", "location", "place_reference", mode="before")
    @classmethod
    def clean_optional_text(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip() or None
        return value

    @field_validator("requested_result_count")
    @classmethod
    def clamp_result_count(cls, value: int | None) -> int | None:
        if value is None:
            return None
        if isinstance(value, bool):
            raise ValueError("requested_result_count must be an integer.")
        return max(1, min(20, value))

    @model_validator(mode="after")
    def validate_action_fields(self) -> "IntentAnalysis":
        if self.action == ParserAction.SEARCH_PLACES and not self.search_terms:
            raise ValueError("Place searches require search terms.")
        if self.action == ParserAction.SELECT_PLACE:
            if self.selected_result_index is None and not self.place_reference:
                raise ValueError("Place selection requires a reference.")
        if self.action not in {
            ParserAction.ANSWER_FROM_CONTEXT,
            ParserAction.SELECT_PLACE,
            ParserAction.GET_PLACE_DETAILS,
        } and self.selected_result_index is not None:
            raise ValueError(
                "Result index is only valid for selection or place details."
            )
        return self


class NaturalResponse(BaseModel):
    message: Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=1, max_length=500),
    ]

    model_config = ConfigDict(extra="forbid")


class ChatResponse(BaseModel):
    message: str
    intent: ChatIntent
    requires_location: bool
    search_query: str | None
    places: list[Place]
    context: SearchContext | None = None
    selected_place_id: str | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "message": (
                        "Berdasarkan tingkat harga Google Maps, saya "
                        "menemukan 1 opsi yang cenderung lebih terjangkau."
                    ),
                    "intent": "place_refinement",
                    "requires_location": False,
                    "search_query": "bakso murah di Gadog, Kabupaten Bogor",
                    "places": [],
                    "context": {
                        "last_intent": "place_refinement",
                        "last_search_terms": "bakso",
                        "last_location": "Gadog, Kabupaten Bogor",
                        "last_search_query": (
                            "bakso murah di Gadog, Kabupaten Bogor"
                        ),
                        "last_place_ids": [],
                        "last_places": [],
                    },
                }
            ]
        }
    )
