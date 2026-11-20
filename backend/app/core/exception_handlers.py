import logging
from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


async def http_exception_handler(
    _request: Request, exception: StarletteHTTPException
) -> JSONResponse:
    return JSONResponse(
        status_code=exception.status_code,
        content={
            "success": False,
            "data": None,
            "error": {
                "code": f"http_{exception.status_code}",
                "message": str(exception.detail),
                "details": None,
            },
        },
        headers=exception.headers,
    )


async def validation_exception_handler(
    _request: Request, exception: RequestValidationError
) -> JSONResponse:
    details: list[dict[str, Any]] = [
        {
            "field": ".".join(str(part) for part in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        }
        for error in exception.errors()
    ]
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "data": None,
            "error": {
                "code": "validation_error",
                "message": "Request validation failed",
                "details": details,
            },
        },
    )


async def unhandled_exception_handler(
    _request: Request, exception: Exception
) -> JSONResponse:
    logger.error(
        "Unhandled API exception",
        exc_info=(type(exception), exception, exception.__traceback__),
    )
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "data": None,
            "error": {
                "code": "internal_server_error",
                "message": "An unexpected error occurred",
                "details": None,
            },
        },
    )