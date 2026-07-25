from functools import lru_cache
from typing import Annotated, Any

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

    @field_validator("places_rate_limit")
    @classmethod
    def validate_rate_limit(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("PLACES_RATE_LIMIT must not be empty.")
        return cleaned


@lru_cache
def get_settings() -> Settings:
    return Settings()
