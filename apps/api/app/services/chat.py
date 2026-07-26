import math
import re

from fastapi import Request

from app.core.exceptions import OllamaError, OllamaInvalidResponseError
from app.schemas.chat import (
    ChatIntent,
    ChatLanguage,
    ChatRequest,
    ChatResponse,
    IntentAnalysis,
    ParserAction,
    RefinementFlags,
    RequestedDetail,
    SearchContext,
    PlaceReference,
)
from app.services.google_places import GooglePlacesService
from app.services.ollama import OllamaService
from app.schemas.place import Place

_PLACE_KEYWORDS = (
    "restoran",
    "rumah sakit",
    "hotel",
    "atm",
    "tempat makan",
    "kafe",
    "cafe",
    "coffee shop",
    "tempat wisata",
    "apotek",
    "spbu",
    "restaurant",
    "hospital",
    "pharmacy",
    "gas station",
    "places to visit",
    "bakso",
    "mie ayam",
    "kopi",
    "ngopi",
    "makan",
    "kuliner",
    "food",
    "mall",
    "museum",
    "pantai",
    "beach",
)
_INDONESIAN_MARKERS = (
    "halo",
    "hai",
    "kamu",
    "siapa",
    "cari",
    "terdekat",
    "dekat sini",
    "rumah sakit",
    "tempat",
    "apotek",
    "restoran",
    "murah",
    "bagus",
    "buka",
    "berapa",
    "harga",
    "yang",
    "makasih",
    "terima kasih",
    "oke",
    "sip",
    "woy",
    "woi",
    "lakuin",
)
_GENERAL_MARKERS = (
    "halo",
    "hai",
    "hello",
    "kamu bisa apa",
    "what can you do",
    "siapa kamu",
    "who are you",
    "makasih",
    "terima kasih",
    "thank you",
    "thanks",
    "woy",
    "woi",
    "hey",
    "apa yang bisa",
    "apa yg bisa",
    "bisa lo",
    "bisa lu",
    "bisa kamu",
    "what do you do",
    "how can you help",
)
_LOCATION_PATTERNS = (
    re.compile(r"\b(?:di|sekitar|dekat)\s+(.+)$", re.IGNORECASE),
    re.compile(r"\b(?:near|in|around)\s+(.+)$", re.IGNORECASE),
)
_NON_LOCATIONS = {
    "me",
    "here",
    "nearby",
    "sini",
    "saya",
    "aku",
    "mana",
    "situ",
}
_ACTION_PREFIX = re.compile(
    r"^(?:tolong\s+)?(?:cari(?:kan)?|temukan|find|show me)\s+",
    re.IGNORECASE,
)

_CHEAPER_TRIGGERS = (
    "murah",
    "lebih murah",
    "budget",
    "affordable",
    "inexpensive",
    "cheaper",
    "ekonomis",
    "ramah kantong",
)
_RATED_TRIGGERS = (
    "rating tertinggi",
    "paling bagus",
    "review terbaik",
    "highest rated",
    "best reviewed",
)
_OPEN_TRIGGERS = (
    "masih buka",
    "buka sekarang",
    "open now",
    "currently open",
)
_ALT_TRIGGERS = (
    "opsi lain",
    "cari yang lain",
    "yang lain",
    "anything else",
    "show more",
)
_NEAREST_TRIGGERS = ("nearest", "closest", "terdekat", "paling dekat")
_OPEN_24_TRIGGERS = ("24 jam", "24 hours", "open all night")
_PRICE_QUESTION_TRIGGERS = (
    "kisaran harga",
    "berapa harganya",
    "price range",
    "how much",
    "menu berapa",
    "budget berapa",
)
_CLOSING_TRIGGERS = (
    "jam berapa tutup",
    "buka sampai jam berapa",
    "what time does",
    "when does",
)
_ACKNOWLEDGEMENTS = {
    "makasih",
    "terima kasih",
    "thanks",
    "thank you",
    "oke",
    "ok",
    "sip",
    "noted",
    "got it",
    "mantap",
    "nice",
}
_CATEGORY_SPECS = (
    (
        ("restaurant", "restoran"),
        {"restaurant"},
        ("restaurants",),
    ),
    (
        ("club", "bar"),
        {"bar", "night_club", "cocktail_bar"},
        ("bars", "night clubs"),
    ),
    (
        ("hotel",),
        {"hotel", "lodging", "resort_hotel"},
        ("hotels",),
    ),
    (
        ("gas station", "pom bensin", "spbu"),
        {"gas_station"},
        ("gas stations",),
    ),
    (
        ("cafe", "kafe", "coffee"),
        {"cafe", "coffee_shop"},
        ("coffee shops",),
    ),
)


class ChatService:
    def __init__(
        self,
        ollama: OllamaService,
        google_places: GooglePlacesService,
    ) -> None:
        self._ollama = ollama
        self._google_places = google_places

    async def chat(self, request: ChatRequest) -> ChatResponse:
        has_coordinates = request.user_lat is not None
        try:
            analysis = await self._ollama.parse_intent(
                request.message,
                has_coordinates=has_coordinates,
                preferred_language=request.language,
                history=request.history,
                context=request.context,
            )
        except OllamaError as exc:
            deterministic_analysis = _deterministic_conversation_analysis(
                request.message,
                request.context,
            )
            if deterministic_analysis is not None:
                analysis = deterministic_analysis
            elif isinstance(exc, OllamaInvalidResponseError):
                analysis = _fallback_analysis(
                    request.message,
                    has_coordinates=has_coordinates,
                    context=request.context,
                )
                if analysis is None:
                    raise
            else:
                raise

        response_language = request.language or analysis.language

        if analysis.action == ParserAction.ACKNOWLEDGE:
            fallback = _acknowledgement_message(response_language)
            reply = await _conversation_reply(
                self._ollama,
                request,
                response_language,
                action=analysis.action,
                response_style=analysis.response_style,
                fallback=fallback,
            )
            return ChatResponse(
                message=reply,
                intent="general",
                requires_location=False,
                search_query=None,
                places=[],
                context=request.context,
            )

        if analysis.action == ParserAction.GENERAL:
            fallback = (
                _safe_general_fallback(request.message, response_language)
                or _generic_general_fallback(response_language)
            )
            reply = await _conversation_reply(
                self._ollama,
                request,
                response_language,
                action=analysis.action,
                response_style=analysis.response_style,
                fallback=fallback,
            )
            return ChatResponse(
                message=reply,
                intent="general",
                requires_location=False,
                search_query=None,
                places=[],
                context=request.context,
            )

        if analysis.action == ParserAction.ASK_CLARIFICATION:
            fallback = (
                analysis.clarification_reason
                or _clarification_message(response_language)
            )
            reply = await _natural_response(
                self._ollama,
                request,
                analysis,
                response_language,
                factual_result={"clarification_required": True},
                limitations=[fallback],
                fallback=fallback,
            )
            return ChatResponse(
                message=reply,
                intent="general",
                requires_location=False,
                search_query=None,
                places=[],
                context=request.context,
            )

        if analysis.action == ParserAction.ANSWER_FROM_CONTEXT:
            (
                factual_result,
                limitations,
                fallback,
                selected_place_id,
            ) = _contextual_answer(
                request.context,
                analysis,
                response_language,
            )
            reply = await _natural_response(
                self._ollama,
                request,
                analysis,
                response_language,
                factual_result=factual_result,
                limitations=limitations,
                fallback=fallback,
                reject_exact_prices=(
                    analysis.requested_detail == RequestedDetail.PRICE_RANGE
                ),
            )
            return ChatResponse(
                message=reply,
                intent="place_detail",
                requires_location=False,
                search_query=None,
                places=[],
                context=request.context,
                selected_place_id=selected_place_id,
            )

        if analysis.action == ParserAction.UNSUPPORTED:
            return ChatResponse(
                message=_unsupported_message(response_language),
                intent="unsupported",
                requires_location=False,
                search_query=None,
                places=[],
                context=request.context,
            )

        if analysis.action in {
            ParserAction.SELECT_PLACE,
            ParserAction.GET_PLACE_DETAILS,
        }:
            matched = _resolve_place_reference(
                request.context,
                analysis.place_reference,
                analysis.selected_result_index,
            )
            if matched is None:
                return ChatResponse(
                    message=_unmatched_place_message(response_language),
                    intent="place_detail",
                    requires_location=False,
                    search_query=None,
                    places=[],
                    context=request.context,
                )
            if (
                analysis.action == ParserAction.SELECT_PLACE
                and analysis.requested_detail == RequestedDetail.NONE
            ):
                fallback = _selected_place_message(
                    matched.name, response_language
                )
                reply = await _natural_response(
                    self._ollama,
                    request,
                    analysis,
                    response_language,
                    factual_result={
                        "selected_place": {
                            "place_id": matched.place_id,
                            "name": matched.name,
                        }
                    },
                    limitations=[],
                    fallback=fallback,
                )
                return ChatResponse(
                    message=reply,
                    intent="place_detail",
                    requires_location=False,
                    search_query=None,
                    places=[],
                    context=request.context,
                    selected_place_id=matched.place_id,
                )
            place = await self._google_places.get_place_details(matched.place_id)
            fallback = _detail_message(
                place, analysis.requested_detail, response_language
            )
            factual_result, limitations = _detail_factual_result(
                place, analysis.requested_detail
            )
            reply = await _natural_response(
                self._ollama,
                request,
                analysis,
                response_language,
                factual_result=factual_result,
                limitations=limitations,
                fallback=fallback,
            )
            return ChatResponse(
                message=reply,
                intent="place_detail",
                requires_location=False,
                search_query=None,
                places=[place],
                context=request.context,
                selected_place_id=place.place_id,
            )

        intent: ChatIntent = (
            "place_search"
            if analysis.action == ParserAction.SEARCH_PLACES
            else "place_refinement"
        )
        last_terms = request.context.last_search_terms if request.context else None
        last_loc = request.context.last_location if request.context else None
        search_terms = analysis.search_terms
        location = _verified_location(analysis.location, request.message)
        explicit_location = _extract_explicit_location(request.message)
        if location is None:
            location = explicit_location
        elif explicit_location and _is_more_specific_location(
            explicit_location,
            location,
        ):
            location = explicit_location

        if intent == "place_refinement":
            search_terms = search_terms or last_terms
            location = location or last_loc
            if not search_terms:
                return ChatResponse(
                    message=_missing_refinement_context_message(
                        analysis.refinements, response_language
                    ),
                    intent="place_refinement",
                    requires_location=False,
                    search_query=None,
                    places=[],
                    context=request.context,
                )

        effective_user_lat = request.user_lat
        effective_user_lng = request.user_lng
        if effective_user_lat is None and request.context and request.context.reference_lat is not None:
            effective_user_lat = request.context.reference_lat
            effective_user_lng = request.context.reference_lng

        has_coordinates = effective_user_lat is not None and effective_user_lng is not None

        if location is None and not has_coordinates:
            return ChatResponse(
                message=_clarification_message(response_language),
                intent=intent,
                requires_location=True,
                search_query=None,
                places=[],
                context=request.context,
            )

        effective_terms = search_terms or request.message
        lowered_terms = effective_terms.casefold()
        if analysis.refinements.cheaper and not any(
            term in lowered_terms for term in ("murah", "cheap", "affordable", "inexpensive")
        ):
            effective_terms = f"{effective_terms} {'murah' if response_language == 'id' else 'affordable'}"
        if analysis.refinements.family_friendly and "family" not in lowered_terms:
            effective_terms = f"{effective_terms} family friendly"
        if analysis.refinements.open_24_hours and "24" not in lowered_terms:
            effective_terms = f"{effective_terms} 24 jam"

        search_query = _build_search_query(effective_terms, location, analysis.language)
        result_count = analysis.requested_result_count or 5
        result_count = max(1, min(20, result_count))
        price_levels = (
            ["PRICE_LEVEL_INEXPENSIVE"]
            if analysis.refinements.cheaper
            else None
        )
        open_now_filter = analysis.refinements.open_now

        places = await self._google_places.search_text(
            search_query,
            user_lat=effective_user_lat,
            user_lng=effective_user_lng,
            price_levels=price_levels,
            open_now=open_now_filter,
            max_results=result_count,
        )

        if analysis.refinements.cheaper and not places:
            places = await self._google_places.search_text(
                search_query,
                user_lat=effective_user_lat,
                user_lng=effective_user_lng,
                price_levels=["PRICE_LEVEL_INEXPENSIVE", "PRICE_LEVEL_MODERATE"],
                open_now=open_now_filter,
                max_results=result_count,
            )

        category_spec = _category_spec(search_terms)
        removed_mismatched_type = False
        if category_spec is not None:
            allowed_types, supplemental_terms = category_spec
            filtered_places = [
                place
                for place in places
                if place.primary_type in allowed_types
            ]
            removed_mismatched_type = len(filtered_places) != len(places)
            places = filtered_places

            should_supplement = len(places) < result_count and (
                removed_mismatched_type
                or analysis.requested_result_count is not None
                or analysis.refinements.nearest
            )
            if should_supplement:
                seen_place_ids = {place.place_id for place in places}
                for supplemental_term in supplemental_terms:
                    supplemental_query = _build_search_query(
                        supplemental_term,
                        location,
                        "en",
                    )
                    supplemental_places = (
                        await self._google_places.search_text(
                            supplemental_query,
                            user_lat=effective_user_lat,
                            user_lng=effective_user_lng,
                            price_levels=price_levels,
                            open_now=open_now_filter,
                            max_results=result_count,
                        )
                    )
                    for place in supplemental_places:
                        if (
                            place.primary_type not in allowed_types
                            or place.place_id in seen_place_ids
                        ):
                            continue
                        seen_place_ids.add(place.place_id)
                        places.append(place)
                        if len(places) >= result_count:
                            break
                    if len(places) >= result_count:
                        break

        if analysis.refinements.open_now:
            places = [place for place in places if place.open_now is True]
        if analysis.refinements.open_24_hours:
            places = [place for place in places if _is_open_24_hours(place)]
        if analysis.refinements.higher_rated:
            places.sort(
                key=lambda p: (p.rating or 0.0, p.user_rating_count or 0),
                reverse=True,
            )
        if analysis.refinements.alternatives and request.context and request.context.last_place_ids:
            previous_ids = set(request.context.last_place_ids)
            alternatives = [place for place in places if place.place_id not in previous_ids]
            if alternatives:
                places = alternatives

        reference_lat = effective_user_lat
        reference_lng = effective_user_lng
        if analysis.refinements.nearest:
            if reference_lat is None and request.context:
                reference_lat = request.context.reference_lat
                reference_lng = request.context.reference_lng
            if reference_lat is None and location:
                reference = await self._google_places.search_text(location, max_results=1)
                if reference:
                    reference_lat, reference_lng = reference[0].lat, reference[0].lng
            if reference_lat is None or reference_lng is None:
                return ChatResponse(
                    message=_nearest_clarification_message(response_language),
                    intent="place_refinement",
                    requires_location=True,
                    search_query=None,
                    places=[],
                    context=request.context,
                )
            for place in places:
                place.distance_meters = _haversine_meters(
                    reference_lat, reference_lng, place.lat, place.lng
                )
            places.sort(
                key=lambda p: (
                    p.distance_meters if p.distance_meters is not None else float("inf"),
                    -(p.rating or 0.0),
                    -(p.user_rating_count or 0),
                )
            )

        places = places[:result_count]
        if analysis.refinements.open_24_hours and not places:
            message = _no_24_hour_message(response_language)
        elif analysis.refinements.cheaper:
            message = _cheaper_result_message(
                len(places), search_terms or "", location, response_language
            )
        elif analysis.refinements.higher_rated:
            message = _higher_rated_message(response_language)
        else:
            message = _result_message(len(places), search_query, response_language)

        new_context = SearchContext(
            last_intent=intent,
            last_search_terms=search_terms,
            last_location=location,
            last_search_query=search_query,
            last_place_ids=[place.place_id for place in places[:10]],
            last_places=[
                {
                    "place_id": place.place_id,
                    "name": place.name,
                    "lat": place.lat,
                    "lng": place.lng,
                    "price_level": place.price_level,
                    "rating": place.rating,
                    "user_rating_count": place.user_rating_count,
                    "open_now": place.open_now,
                }
                for place in places[:10]
            ],
            reference_lat=reference_lat,
            reference_lng=reference_lng,
        )
        return ChatResponse(
            message=message,
            intent=intent,
            requires_location=False,
            search_query=search_query,
            places=places,
            context=new_context,
        )


async def _conversation_reply(
    ollama: OllamaService,
    request: ChatRequest,
    language: ChatLanguage,
    *,
    action: ParserAction,
    response_style: str,
    fallback: str,
) -> str:
    try:
        return await ollama.converse(
            request.message,
            language=language,
            action=action,
            response_style=response_style,
            history=request.history,
        )
    except OllamaError:
        return fallback


async def _natural_response(
    ollama: OllamaService,
    request: ChatRequest,
    analysis: IntentAnalysis,
    language: ChatLanguage,
    *,
    factual_result: dict[str, object],
    limitations: list[str],
    fallback: str,
    reject_exact_prices: bool = False,
) -> str:
    try:
        reply = await ollama.respond(
            request.message,
            language=language,
            action=analysis.action,
            factual_result=factual_result,
            limitations=limitations,
            history=request.history,
            context=request.context,
            response_style=analysis.response_style,
        )
    except OllamaError:
        return fallback

    if reject_exact_prices and re.search(
        r"(?:\brp\s*[\d.]|\b\d+\s*(?:ribu|rb|k)\b)",
        reply.casefold(),
    ):
        return fallback
    return reply


def _deterministic_conversation_analysis(
    message: str,
    context: SearchContext | None,
) -> IntentAnalysis | None:
    lowered = " ".join(message.casefold().strip(" .,!?\t\r\n").split())
    language = _detect_language(lowered)
    selected_index = _extract_result_index(lowered)
    place_reference = _mentioned_place_name(message, context)

    if _is_acknowledgement(message):
        return _conversation_analysis(
            ParserAction.ACKNOWLEDGE,
            language,
        )

    asks_price = any(
        trigger in lowered for trigger in _PRICE_QUESTION_TRIGGERS
    ) or (
        "kisaran" in lowered
        and any(marker in lowered for marker in ("harga", "harganya"))
    )
    asks_price = asks_price or (
        context is not None
        and "murah semua" in lowered
        and any(marker in lowered for marker in ("tadi", "tempat", "hasil"))
    )
    if asks_price:
        return _conversation_analysis(
            ParserAction.ANSWER_FROM_CONTEXT,
            language,
            requested_detail=RequestedDetail.PRICE_RANGE,
            selected_result_index=selected_index,
            place_reference=place_reference,
        )

    asks_closing = any(
        trigger in lowered for trigger in _CLOSING_TRIGGERS
    ) and any(
        marker in lowered for marker in ("tutup", "close", "buka sampai")
    )
    if asks_closing:
        return _conversation_analysis(
            ParserAction.GET_PLACE_DETAILS,
            language,
            requested_detail=RequestedDetail.CLOSING_TIME,
            selected_result_index=selected_index,
            place_reference=place_reference,
        )

    if context and context.last_places:
        if (
            ("rating" in lowered or any(t in lowered for t in _RATED_TRIGGERS))
            and any(
                marker in lowered
                for marker in ("mana", "which", "tadi", "pertama", "kedua", "ketiga")
            )
        ):
            return _conversation_analysis(
                ParserAction.ANSWER_FROM_CONTEXT,
                language,
                requested_detail=RequestedDetail.RATING,
                selected_result_index=selected_index,
                place_reference=place_reference,
            )

        asks_name = (
            selected_index is not None
            and any(marker in lowered for marker in ("nama", "name"))
        )
        if asks_name:
            return _conversation_analysis(
                ParserAction.ANSWER_FROM_CONTEXT,
                language,
                selected_result_index=selected_index,
            )

        asks_open_status = (
            any(trigger in lowered for trigger in _OPEN_TRIGGERS)
            and any(marker in lowered for marker in ("mana", "which", "tadi"))
        )
        if asks_open_status:
            return _conversation_analysis(
                ParserAction.ANSWER_FROM_CONTEXT,
                language,
                requested_detail=RequestedDetail.OPENING_HOURS,
                selected_result_index=selected_index,
                place_reference=place_reference,
            )

        detail = RequestedDetail.NONE
        if any(marker in lowered for marker in ("alamat", "address")):
            detail = RequestedDetail.ADDRESS
        elif any(
            marker in lowered
            for marker in ("directions", "direction", "rute", "petunjuk arah")
        ):
            detail = RequestedDetail.DIRECTIONS
        if detail != RequestedDetail.NONE:
            return _conversation_analysis(
                ParserAction.GET_PLACE_DETAILS,
                language,
                requested_detail=detail,
                selected_result_index=selected_index,
                place_reference=place_reference,
            )

        if selected_index is not None and len(lowered.split()) <= 6:
            return _conversation_analysis(
                ParserAction.SELECT_PLACE,
                language,
                selected_result_index=selected_index,
                place_reference=place_reference,
            )
    if _is_obvious_general(message):
        return _conversation_analysis(ParserAction.GENERAL, language)
    return None


def _conversation_analysis(
    action: ParserAction,
    language: ChatLanguage,
    *,
    requested_detail: RequestedDetail = RequestedDetail.NONE,
    selected_result_index: int | None = None,
    place_reference: str | None = None,
) -> IntentAnalysis:
    return IntentAnalysis(
        action=action,
        search_terms=None,
        location=None,
        language=language,
        requested_result_count=None,
        place_reference=place_reference,
        selected_result_index=selected_result_index,
        requested_detail=requested_detail,
        refinements=RefinementFlags(),
        requires_clarification=False,
    )


def _is_acknowledgement(message: str) -> bool:
    normalized = " ".join(message.casefold().strip(" .,!?\t\r\n").split())
    if normalized in _ACKNOWLEDGEMENTS:
        return True
    return normalized in {
        "oke makasih",
        "ok makasih",
        "sip makasih",
        "okay thanks",
        "ok thanks",
    }


def _extract_result_index(lowered: str) -> int | None:
    ordinal_words = {
        "pertama": 1,
        "kedua": 2,
        "ketiga": 3,
        "first": 1,
        "second": 2,
        "third": 3,
    }
    for word, index in ordinal_words.items():
        if re.search(rf"\b{word}\b", lowered):
            return index

    word_match = re.search(
        r"\b(?:nomor|no|tempat|hasil|result)\s+"
        r"(satu|dua|tiga|one|two|three|[1-9]|10)\b",
        lowered,
    )
    if not word_match:
        return None
    value = word_match.group(1)
    words = {
        "satu": 1,
        "dua": 2,
        "tiga": 3,
        "one": 1,
        "two": 2,
        "three": 3,
    }
    return words.get(value, int(value) if value.isdigit() else None)


def _mentioned_place_name(
    message: str,
    context: SearchContext | None,
) -> str | None:
    if not context:
        return None
    normalized_message = _normalize_name(message)
    matches = [
        place.name
        for place in context.last_places
        if _normalize_name(place.name) in normalized_message
    ]
    return matches[0] if len(matches) == 1 else None


def _contextual_answer(
    context: SearchContext | None,
    analysis: IntentAnalysis,
    language: ChatLanguage,
) -> tuple[dict[str, object], list[str], str, str | None]:
    references = list(context.last_places) if context else []
    selected = _resolve_place_reference(
        context,
        analysis.place_reference,
        analysis.selected_result_index,
    )
    selected_place_id = selected.place_id if selected else None
    if analysis.selected_result_index is not None or analysis.place_reference:
        references = [selected] if selected else []

    if not references:
        limitation = (
            "No previous place results are available for this question."
        )
        return (
            {"places": [], "data_available": False},
            [limitation],
            _unmatched_place_message(language),
            selected_place_id,
        )

    if analysis.requested_detail == RequestedDetail.PRICE_RANGE:
        place_facts = [
            {"name": place.name, "price_level": place.price_level}
            for place in references
        ]
        limitation = (
            "Google Places provides categorical price levels, not exact menu "
            "prices."
        )
        details = ", ".join(
            f"{place.name}: {_price_level_label(place.price_level, language)}"
            for place in references
        )
        if language == "id":
            fallback = (
                "Google Maps hanya menyediakan kategori harga kasar, bukan "
                f"harga menu aktual. {details}."
            )
        else:
            fallback = (
                "Google Maps only provides broad price categories, not exact "
                f"menu prices. {details}."
            )
        return (
            {
                "exact_menu_prices_available": False,
                "price_level_available": any(
                    place.price_level is not None for place in references
                ),
                "places": place_facts,
            },
            [limitation],
            fallback,
            selected_place_id,
        )

    if analysis.requested_detail == RequestedDetail.RATING:
        rated = [place for place in references if place.rating is not None]
        highest = max(
            rated,
            key=lambda place: (
                place.rating or 0.0,
                place.user_rating_count or 0,
            ),
            default=None,
        )
        facts = [
            {
                "name": place.name,
                "rating": place.rating,
                "user_rating_count": place.user_rating_count,
            }
            for place in references
        ]
        if highest:
            fallback = (
                f"Dari hasil sebelumnya, rating tertinggi adalah "
                f"{highest.name} ({highest.rating:.1f})."
                if language == "id"
                else f"From the previous results, {highest.name} has the "
                f"highest rating ({highest.rating:.1f})."
            )
        else:
            fallback = (
                "Rating untuk hasil sebelumnya belum tersedia."
                if language == "id"
                else "Ratings are not available for the previous results."
            )
        return (
            {"places": facts, "highest_rated": highest.name if highest else None},
            [] if highest else ["Rating data is unavailable."],
            fallback,
            selected_place_id,
        )

    if analysis.requested_detail == RequestedDetail.OPENING_HOURS:
        open_places = [place.name for place in references if place.open_now is True]
        unknown_places = [
            place.name for place in references if place.open_now is None
        ]
        if open_places:
            names = ", ".join(open_places)
            fallback = (
                f"Yang tercatat masih buka dari hasil sebelumnya: {names}."
                if language == "id"
                else f"Listed as currently open: {names}."
            )
        else:
            fallback = (
                "Tidak ada hasil sebelumnya yang dapat diverifikasi masih buka."
                if language == "id"
                else "None of the previous results can be verified as open now."
            )
        return (
            {
                "open_now": open_places,
                "unknown_open_status": unknown_places,
            },
            (
                ["Open status can change and may be unavailable."]
                if unknown_places
                else []
            ),
            fallback,
            selected_place_id,
        )

    if selected:
        fallback = _selected_place_message(selected.name, language)
        return (
            {
                "selected_place": {
                    "place_id": selected.place_id,
                    "name": selected.name,
                }
            },
            [],
            fallback,
            selected_place_id,
        )

    limitation = "The requested detail is unavailable in the previous results."
    fallback = (
        "Detail tersebut belum tersedia dari hasil sebelumnya."
        if language == "id"
        else "That detail is not available in the previous results."
    )
    return (
        {"places": [], "data_available": False},
        [limitation],
        fallback,
        selected_place_id,
    )


def _price_level_label(
    price_level: str | None,
    language: ChatLanguage,
) -> str:
    labels = {
        "PRICE_LEVEL_FREE": ("gratis", "free"),
        "PRICE_LEVEL_INEXPENSIVE": ("terjangkau", "inexpensive"),
        "PRICE_LEVEL_MODERATE": ("menengah", "moderate"),
        "PRICE_LEVEL_EXPENSIVE": ("mahal", "expensive"),
        "PRICE_LEVEL_VERY_EXPENSIVE": ("sangat mahal", "very expensive"),
    }
    if price_level not in labels:
        return "belum tersedia" if language == "id" else "unavailable"
    return labels[price_level][0 if language == "id" else 1]


def _detail_factual_result(
    place: Place,
    detail: RequestedDetail,
) -> tuple[dict[str, object], list[str]]:
    facts: dict[str, object] = {
        "place_id": place.place_id,
        "name": place.name,
        "requested_detail": detail.value,
    }
    limitations: list[str] = []
    if detail in {RequestedDetail.CLOSING_TIME, RequestedDetail.OPENING_HOURS}:
        closing = _next_close_time(place)
        facts["verified_closing_time"] = closing
        if closing is None:
            limitations.append(
                "Google Maps does not currently provide a verified closing time."
            )
    elif detail == RequestedDetail.ADDRESS:
        facts["address"] = place.address
        if place.address is None:
            limitations.append("A verified address is unavailable.")
    elif detail == RequestedDetail.RATING:
        facts["rating"] = place.rating
        facts["user_rating_count"] = place.user_rating_count
        if place.rating is None:
            limitations.append("A verified rating is unavailable.")
    elif detail == RequestedDetail.DIRECTIONS:
        facts["directions_url"] = place.directions_url
    elif detail == RequestedDetail.PRICE_RANGE:
        facts["price_level"] = place.price_level
        facts["exact_menu_prices_available"] = False
        limitations.append(
            "Google Places provides categorical price levels, not exact menu prices."
        )
    return facts, limitations


def _acknowledgement_message(language: ChatLanguage) -> str:
    if language == "id":
        return "Sama-sama! Kalau mau cari tempat lain, tinggal bilang aja."
    return "You're welcome! Tell me what kind of place you want to find next."


def _selected_place_message(name: str, language: ChatLanguage) -> str:
    if language == "id":
        return f"Pilihan tersebut adalah {name}."
    return f"That result is {name}."



def get_chat_service(request: Request) -> ChatService:
    settings = request.app.state.settings
    client = request.app.state.http_client
    return ChatService(
        ollama=OllamaService(settings=settings, client=client),
        google_places=GooglePlacesService(settings=settings, client=client),
    )


def _fallback_analysis(
    message: str,
    *,
    has_coordinates: bool,
    context: SearchContext | None = None,
) -> IntentAnalysis | None:
    lowered = message.casefold()
    language = _detect_language(lowered)
    conversational = _deterministic_conversation_analysis(message, context)
    if conversational is not None:
        return conversational
    if _is_obvious_general(message):
        return _conversation_analysis(ParserAction.GENERAL, language)

    # Check for refinement triggers if context exists
    if context and (context.last_search_terms or context.last_location):
        refinements = RefinementFlags(
            cheaper=any(t in lowered for t in _CHEAPER_TRIGGERS),
            higher_rated=any(t in lowered for t in _RATED_TRIGGERS),
            open_now=any(t in lowered for t in _OPEN_TRIGGERS),
            open_24_hours=any(t in lowered for t in _OPEN_24_TRIGGERS),
            nearest=any(t in lowered for t in _NEAREST_TRIGGERS),
            alternatives=any(t in lowered for t in _ALT_TRIGGERS),
        )
        requested_count = _extract_requested_count(lowered)

        if refinements.any_enabled() or requested_count is not None:
            location = _extract_explicit_location(message) or context.last_location
            terms = _strip_action_and_location(message)
            if not terms or terms in _CHEAPER_TRIGGERS or terms in _RATED_TRIGGERS:
                terms = context.last_search_terms

            return IntentAnalysis(
                action=ParserAction.REFINE_SEARCH,
                search_terms=terms,
                location=location,
                language=language,
                requested_result_count=requested_count,
                place_reference=None,
                selected_result_index=None,
                requested_detail=RequestedDetail.NONE,
                refinements=refinements,
                requires_clarification=False,
            )

    if not any(keyword in lowered for keyword in _PLACE_KEYWORDS):
        return None

    location = _extract_explicit_location(message)
    terms = _strip_action_and_location(message)
    if not terms:
        return None

    return IntentAnalysis(
        action=ParserAction.SEARCH_PLACES,
        search_terms=terms,
        location=location,
        language=language,
        requested_result_count=None,
        place_reference=None,
        selected_result_index=None,
        requested_detail=RequestedDetail.NONE,
        refinements=RefinementFlags(),
        requires_clarification=location is None and not has_coordinates,
    )


def _extract_requested_count(lowered: str) -> int | None:
    digit_match = re.search(r"\b(\d{1,2})\b", lowered)
    if digit_match:
        return max(1, min(20, int(digit_match.group(1))))
    words = {
        "one": 1, "two": 2, "three": 3, "five": 5, "ten": 10,
        "satu": 1, "dua": 2, "tiga": 3, "lima": 5, "sepuluh": 10,
    }
    for word, value in words.items():
        if re.search(rf"\b{word}\b", lowered):
            return value
    return None


def _detect_language(lowered_message: str) -> ChatLanguage:
    if re.search(
        r"\b(?:bro|brow|woy|woi|gue|gua|lu|lo|yg)\b",
        lowered_message,
    ):
        return "id"
    if any(marker in lowered_message for marker in _INDONESIAN_MARKERS):
        return "id"
    return "en"


def _is_obvious_general(message: str) -> bool:
    lowered = message.casefold()
    has_general_marker = any(marker in lowered for marker in _GENERAL_MARKERS)
    has_general_marker = has_general_marker or bool(
        re.search(r"\b(?:hi|hai|halo|hello|hey|yo|woy|woi|bro|brow)\b", lowered)
    )
    return has_general_marker and not _has_place_request_signal(message)


def _has_place_request_signal(message: str) -> bool:
    lowered = message.casefold()
    if any(keyword in lowered for keyword in _PLACE_KEYWORDS):
        return True
    if re.search(
        r"\b(?:cari(?:in|kan)?|carikan|temukan|rekomendasi(?:in)?|"
        r"find|recommend|show me)\b",
        lowered,
    ):
        return True
    return any(
        marker in lowered
        for marker in (
            "dekat sini",
            "di sekitar",
            "near me",
            "nearby",
            "around here",
        )
    )


def _acknowledgement_reply(
    message: str, language: ChatLanguage
) -> str | None:
    lowered = message.casefold()
    if not any(
        marker in lowered
        for marker in ("makasih", "terima kasih", "thank you", "thanks")
    ):
        return None
    if language == "id":
        return "Sama-sama! Kalau mau mencari tempat lain, tinggal bilang saja."
    return "You're welcome! Tell me what kind of place you want to find next."


def _safe_general_fallback(
    message: str,
    language: ChatLanguage,
) -> str | None:
    if not _is_obvious_general(message):
        return None

    lowered = message.casefold()
    asks_capability = any(
        marker in lowered
        for marker in (
            "bisa apa",
            "siapa kamu",
            "what can you do",
            "who are you",
            "bisa bantu",
            "can you help",
        )
    )
    is_thanks = any(
        marker in lowered
        for marker in ("makasih", "terima kasih", "thank you", "thanks")
    )
    if language == "id":
        if is_thanks:
            return "Sama-sama! Kalau mau mencari tempat lain, tinggal bilang saja."
        if asks_capability:
            return "Saya membantu mencari tempat terverifikasi dari Google Maps."
        return "Hai! Ada tempat yang ingin kamu cari?"
    if is_thanks:
        return "You're welcome! Tell me what kind of place you want to find next."
    if asks_capability:
        return "I help find verified places using Google Maps data."
    return "Hi! Is there a place you would like to find?"


def _generic_general_fallback(language: ChatLanguage) -> str:
    if language == "id":
        return (
            "Gue belum yakin nangkep maksud lo. Kasih sedikit petunjuk, "
            "nanti gue jawab langsung."
        )
    return (
        "I'm not sure I understood that. Give me a little more context "
        "and I'll answer directly."
    )


def _extract_explicit_location(message: str) -> str | None:
    for pattern in _LOCATION_PATTERNS:
        match = pattern.search(message)
        if not match:
            continue
        candidate = match.group(1).strip(" .,!?\t\r\n")
        if candidate.casefold() not in _NON_LOCATIONS and len(candidate) >= 2:
            return candidate
    return None


def _verified_location(location: str | None, message: str) -> str | None:
    if not location:
        return None
    normalized_location = " ".join(location.casefold().split())
    normalized_message = " ".join(message.casefold().split())
    return location if normalized_location in normalized_message else None


def _is_more_specific_location(candidate: str, planned: str) -> bool:
    normalized_candidate = " ".join(candidate.casefold().split())
    normalized_planned = " ".join(planned.casefold().split())
    if not normalized_candidate.startswith(normalized_planned):
        return False
    suffix = normalized_candidate[len(normalized_planned):]
    return any(
        suffix.startswith(marker)
        for marker in (" dekat ", " near ", " around ", " sekitar ")
    )


def _category_spec(
    search_terms: str | None,
) -> tuple[set[str], tuple[str, ...]] | None:
    if not search_terms:
        return None
    normalized = search_terms.casefold()
    for triggers, allowed_types, supplemental_terms in _CATEGORY_SPECS:
        if any(trigger in normalized for trigger in triggers):
            return allowed_types, supplemental_terms
    return None


def _strip_action_and_location(message: str) -> str:
    without_action = _ACTION_PREFIX.sub("", message.strip())
    for pattern in _LOCATION_PATTERNS:
        match = pattern.search(without_action)
        if match and match.group(1).strip(" .,!?\t\r\n").casefold() not in _NON_LOCATIONS:
            without_action = without_action[: match.start()]
            break
    return without_action.strip(" .,!?\t\r\n")


def _build_search_query(
    search_terms: str,
    location: str | None,
    language: ChatLanguage,
) -> str:
    terms = search_terms.strip()
    if not location or location.casefold() in terms.casefold():
        return terms
    connector = "di" if language == "id" else "near"
    return f"{terms} {connector} {location}"


def _clarification_message(language: ChatLanguage) -> str:
    if language == "id":
        return "Di kota atau area mana saya harus mencari?"
    return "Which city or area should I search in?"


def _missing_refinement_context_message(
    refinements: RefinementFlags, language: ChatLanguage
) -> str:
    if language == "id":
        if refinements.cheaper:
            return "Tempat atau jenis usaha apa yang ingin Anda cari dengan harga lebih terjangkau?"
        return "Jenis tempat apa yang ingin Anda cari?"
    if refinements.cheaper:
        return "Which type of place would you like me to find at a lower price?"
    return "Which type of place would you like to search for?"


def _unsupported_message(language: ChatLanguage) -> str:
    if language == "id":
        return "Saya hanya dapat membantu percakapan singkat dan pencarian tempat."
    return "I can only help with concise conversation and place searches."


def _result_message(count: int, query: str, language: ChatLanguage) -> str:
    if count == 0:
        if language == "id":
            return "Saya tidak menemukan tempat yang cocok untuk pencarian tersebut."
        return "I couldn't find matching places for that search."
    if language == "id":
        return f"Saya menemukan {count} {query}."
    return f"I found {count} {query}."


def _cheaper_result_message(
    count: int, search_terms: str, location: str | None, language: ChatLanguage
) -> str:
    loc_suffix = f" di sekitar {location}" if location else ""
    if language == "id":
        return f"Berdasarkan tingkat harga yang tersedia di Google Maps, saya menemukan {count} opsi {search_terms} yang cenderung lebih terjangkau{loc_suffix}."
    return f"Based on the price level available in Google Maps, I found {count} more affordable options."


def _higher_rated_message(language: ChatLanguage) -> str:
    if language == "id":
        return "Berikut opsi dengan rating tertinggi dari hasil yang tersedia."
    return "Here are the highest rated options from available results."


def _resolve_place_reference(
    context: SearchContext | None,
    reference: str | None,
    selected_index: int | None,
) -> PlaceReference | None:
    if context is None or not context.last_places:
        return None
    if selected_index is not None:
        index = selected_index - 1
        return context.last_places[index] if 0 <= index < len(context.last_places) else None
    if not reference:
        return context.last_places[0] if len(context.last_places) == 1 else None
    normalized = _normalize_name(reference)
    exact = [place for place in context.last_places if _normalize_name(place.name) == normalized]
    if len(exact) == 1:
        return exact[0]
    partial = [
        place for place in context.last_places
        if normalized in _normalize_name(place.name) or _normalize_name(place.name) in normalized
    ]
    return partial[0] if len(partial) == 1 else None


def _normalize_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()


def _is_open_24_hours(place: Place) -> bool:
    for hours in (place.current_opening_hours, place.regular_opening_hours):
        if not isinstance(hours, dict):
            continue
        periods = hours.get("periods")
        if not isinstance(periods, list):
            continue
        for period in periods:
            if not isinstance(period, dict):
                continue
            opened = period.get("open")
            closed = period.get("close")
            if isinstance(opened, dict) and closed is None:
                day = opened.get("day")
                hour = opened.get("hour", 0)
                minute = opened.get("minute", 0)
                if day == 0 and hour == 0 and minute == 0:
                    return True
    return False


def _detail_message(
    place: Place,
    detail: RequestedDetail,
    language: ChatLanguage,
) -> str:
    if detail == RequestedDetail.PRICE_RANGE:
        level = _price_level_label(place.price_level, language)
        if language == "id":
            return (
                "Google Maps hanya menyediakan kategori harga kasar, bukan "
                f"harga menu aktual. {place.name}: {level}."
            )
        return (
            "Google Maps only provides a broad price category, not exact menu "
            f"prices. {place.name}: {level}."
        )
    if detail in {RequestedDetail.CLOSING_TIME, RequestedDetail.OPENING_HOURS}:
        closing = _next_close_time(place)
        if closing:
            return (
                f"{place.name} tercatat tutup pada {closing}."
                if language == "id"
                else f"{place.name} is listed as closing at {closing}."
            )
        return (
            f"Saya menemukan {place.name}, tetapi Google Maps tidak menyediakan waktu tutup terverifikasi saat ini."
            if language == "id"
            else f"I found {place.name}, but Google Maps does not currently provide a verified closing time."
        )
    if detail == RequestedDetail.ADDRESS:
        return (
            f"Alamat {place.name}: {place.address or 'tidak tersedia'}."
            if language == "id"
            else f"{place.name}'s address is {place.address or 'unavailable'}."
        )
    if detail == RequestedDetail.RATING:
        rating = f"{place.rating:.1f}" if place.rating is not None else ("tidak tersedia" if language == "id" else "unavailable")
        return f"Rating {place.name}: {rating}." if language == "id" else f"{place.name} has a rating of {rating}."
    if detail == RequestedDetail.DIRECTIONS:
        return (
            f"Gunakan tombol Directions untuk menuju {place.name}."
            if language == "id"
            else f"Use the Directions action to navigate to {place.name}."
        )
    return f"{place.name}."


def _next_close_time(place: Place) -> str | None:
    for hours in (place.current_opening_hours, place.regular_opening_hours):
        if not isinstance(hours, dict):
            continue
        next_close = hours.get("nextCloseTime")
        if isinstance(next_close, str) and next_close.strip():
            return next_close.strip()
        descriptions = hours.get("weekdayDescriptions")
        if isinstance(descriptions, list) and descriptions:
            return None
    return None


def _haversine_meters(
    lat1: float, lng1: float, lat2: float, lng2: float
) -> float:
    radius = 6_371_000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lng2 - lng1)
    a = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    )
    return radius * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _nearest_clarification_message(language: ChatLanguage) -> str:
    return (
        "Saya memerlukan lokasi Anda atau titik acuan spesifik untuk menentukan tempat terdekat."
        if language == "id"
        else "I need your current location or a specific landmark to determine the nearest place."
    )


def _no_24_hour_message(language: ChatLanguage) -> str:
    return (
        "Saya belum dapat memverifikasi tempat yang buka 24 jam dari hasil ini."
        if language == "id"
        else "I could not verify any of these places as open 24 hours."
    )


def _unmatched_place_message(language: ChatLanguage) -> str:
    return (
        "Saya tidak dapat mencocokkan tempat itu dengan hasil terbaru. Sebutkan nama atau nomor hasilnya."
        if language == "id"
        else "I could not match that place to the latest results. Please mention its name or result number."
    )
