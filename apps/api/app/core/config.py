from functools import lru_cache
from typing import Annotated, Any
from urllib.parse import urlparse

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    google_places_api_key: SecretStr | None = Field(
        default=None,
        validation_alias="GOOGLE_PLACES_API_KEY",
    )
    allowed_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:3000"],
        validation_alias="ALLOWED_ORIGINS",
    )
    app_env: str = Field(default="development", validation_alias="APP_ENV")
    google_places_timeout_seconds: float = Field(
        default=15,
        gt=0,
        validation_alias="GOOGLE_PLACES_TIMEOUT_SECONDS",
    )
    places_rate_limit: str = Field(
        default="30/minute",
        validation_alias="PLACES_RATE_LIMIT",
    )
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        validation_alias="OLLAMA_BASE_URL",
    )
    ollama_model: str = Field(
        default="qwen3:4b",
        validation_alias="OLLAMA_MODEL",
    )
    ollama_conversation_model: str | None = Field(
        default=None,
        validation_alias="OLLAMA_CONVERSATION_MODEL",
    )
    ollama_timeout_seconds: float = Field(
        default=90,
        gt=0,
        validation_alias="OLLAMA_TIMEOUT_SECONDS",
    )
    chat_rate_limit: str = Field(
        default="20/minute",
        validation_alias="CHAT_RATE_LIMIT",
    )
    google_places_location_bias_radius_meters: float = Field(
        default=5000,
        gt=0,
        le=50000,
        validation_alias="GOOGLE_PLACES_LOCATION_BIAS_RADIUS_METERS",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_allowed_origins(cls, value: Any) -> list[str]:
        if isinstance(value, str):
            origins = [origin.strip() for origin in value.split(",")]
        elif isinstance(value, (list, tuple, set)):
            origins = [str(origin).strip() for origin in value]
        else:
            raise ValueError("ALLOWED_ORIGINS must be a comma-separated string.")

        cleaned = list(dict.fromkeys(origin for origin in origins if origin))
        if not cleaned:
            raise ValueError("ALLOWED_ORIGINS must contain at least one origin.")
        if "*" in cleaned:
            raise ValueError("Wildcard CORS origins are not allowed.")
        return cleaned

    @field_validator("places_rate_limit", "chat_rate_limit")
    @classmethod
    def validate_rate_limit(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Rate limits must not be empty.")
        return cleaned

    @field_validator("ollama_base_url")
    @classmethod
    def validate_ollama_base_url(cls, value: str) -> str:
        cleaned = value.strip().rstrip("/")
        parsed = urlparse(cleaned)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("OLLAMA_BASE_URL must be a valid HTTP URL.")
        return cleaned

    @field_validator("ollama_model")
    @classmethod
    def validate_ollama_model(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("OLLAMA_MODEL must not be empty.")
        return cleaned

    @field_validator("ollama_conversation_model", mode="before")
    @classmethod
    def validate_conversation_model(cls, value: Any) -> str | None:
        if value is None:
            return None
        cleaned = str(value).strip()
        return cleaned or None


@lru_cache
def get_settings() -> Settings:
    return Settings()
