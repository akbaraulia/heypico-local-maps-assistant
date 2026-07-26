from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import get_settings

limiter = Limiter(key_func=get_remote_address)


def get_places_rate_limit() -> str:
    return get_settings().places_rate_limit


def get_chat_rate_limit() -> str:
    return get_settings().chat_rate_limit
