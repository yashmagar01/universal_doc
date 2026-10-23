"""RFC 7807 problem details for every HTTP error (architecture §11).

The API contract says errors carry `code` + `hint`; a plain FastAPI `detail` is not
enough. This helper keeps the standard problem members and adds both extensions.
"""

from __future__ import annotations

from http import HTTPStatus
from typing import Any

from fastapi.responses import JSONResponse

DEFAULT_CODES = {
    400: "bad_request",
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    409: "conflict",
    413: "payload_too_large",
    422: "invalid_request",
    500: "internal_error",
}


def problem(
    status: int,
    *,
    hint: str,
    code: str | None = None,
    detail: str | None = None,
    instance: str | None = None,
    headers: dict[str, str] | None = None,
    **extra: Any,
) -> JSONResponse:
    """Build an `application/problem+json` response; `hint` is always user-facing."""
    try:
        title = HTTPStatus(status).phrase
    except ValueError:
        title = "Error"
    content: dict[str, Any] = {
        "type": "about:blank",
        "title": title,
        "status": status,
        "detail": detail or hint,
        "code": code or DEFAULT_CODES.get(status, "error"),
        "hint": hint,
        **extra,
    }
    if instance is not None:
        content["instance"] = instance
    return JSONResponse(
        status_code=status, media_type="application/problem+json", content=content, headers=headers
    )
