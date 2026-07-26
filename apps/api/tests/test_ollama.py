import asyncio
import json

import httpx
from pydantic import SecretStr

from app.core.config import Settings
from app.schemas.chat import ParserAction
from app.services.ollama import OllamaService


def test_conversation_model_does_not_replace_planner_model() -> None:
    requested_models: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        requested_models.append(payload["model"])
        if len(requested_models) == 1:
            content = json.dumps(
                {
                    "action": "general",
                    "search_terms": None,
                    "location": None,
                    "language": "en",
                    "response_style": "neutral",
                    "requested_result_count": None,
                    "place_reference": None,
                    "selected_result_index": None,
                    "requested_detail": "none",
                    "refinements": {
                        "cheaper": False,
                        "higher_rated": False,
                        "open_now": False,
                        "open_24_hours": False,
                        "nearest": False,
                        "alternatives": False,
                        "family_friendly": False,
                    },
                    "requires_clarification": False,
                }
            )
        else:
            content = json.dumps({"message": "I can help with that."})
        return httpx.Response(
            200,
            json={"message": {"role": "assistant", "content": content}},
        )

    async def scenario() -> None:
        settings = Settings(
            google_places_api_key=SecretStr("safe-test-key"),
            app_env="test",
            ollama_model="qwen3:4b",
            ollama_conversation_model="qwen3:8b",
        )
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(handler)
        ) as client:
            service = OllamaService(settings, client)
            await service.parse_intent(
                "What can you do?",
                has_coordinates=False,
                preferred_language=None,
                history=[],
                context=None,
            )
            reply = await service.respond(
                "What can you do?",
                language="en",
                action=ParserAction.GENERAL,
                factual_result={"supported_capabilities": ["place search"]},
                limitations=[],
                history=[],
                context=None,
            )
            assert reply == "I can help with that."

    asyncio.run(scenario())

    assert requested_models == ["qwen3:4b", "qwen3:8b"]
