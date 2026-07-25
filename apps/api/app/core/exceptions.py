import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from app.schemas.error import ErrorDetail, ErrorResponse

logger = logging.getLogger(__name__)


class AppError(Exception):
    def __init__(self, *, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


class GooglePlacesTimeoutError(AppError):
    def __init__(self) -> None:
        super().__init__(
            status_code=504,
            code="google_places_timeout",
            message="Google Places request timed out.",
        )


class GooglePlacesUnavailableError(AppError):
    def __init__(self) -> None:
        super().__init__(
            status_code=503,
            code="google_places_unavailable",
            message="Google Places service is temporarily unavailable.",
        )


class GooglePlacesRequestError(AppError):
    def __init__(self) -> None:
        super().__init__(
            status_code=502,
            code="google_places_request_failed",
            message="Google Places request failed.",
        )


class GooglePlacesMalformedResponseError(AppError):
    def __init__(self) -> None:
        super().__init__(
            status_code=502,
            code="google_places_invalid_response",
            message="Google Places returned an invalid response.",
        )


class ServerConfigurationError(AppError):
    def __init__(self) -> None:
        super().__init__(
            status_code=500,
            code="server_configuration_error",
            message="Server configuration error.",
        )


def _error_response(status_code: int, code: str, message: str) -> JSONResponse:
    payload = ErrorResponse(error=ErrorDetail(code=code, message=message))
    return JSONResponse(status_code=status_code, content=payload.model_dump())


async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
    logger.warning("api_error code=%s status_code=%s", exc.code, exc.status_code)
    return _error_response(exc.status_code, exc.code, exc.message)


async def rate_limit_error_handler(
    _request: Request,
    _exc: RateLimitExceeded,
) -> JSONResponse:
    return _error_response(429, "rate_limit_exceeded", "Rate limit exceeded.")


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(RateLimitExceeded, rate_limit_error_handler)
