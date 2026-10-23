"""FastAPI application factory: security middleware, versioned router (§11, §10.2)."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any, cast

from fastapi import FastAPI, Request, Response
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from ..ingest.job import make_ingest_handler
from ..store import BlobStore, get_engine, init_db
from ..vault import KeyringStore, SecretStore
from .jobs import default_runner
from .logging import configure_logging
from .problems import problem
from .security import (
    COOKIE,
    HEADER,
    LAUNCH_HEADER,
    SECURITY_HEADERS,
    SecurityConfig,
    check_request,
)


def create_app(
    home: Path,
    *,
    token: str | None = None,
    allowed_hostnames: frozenset[str] | None = None,
    vault: SecretStore | None = None,
) -> FastAPI:
    cfg = SecurityConfig(
        token=token or SecurityConfig().token,
        allowed_hostnames=allowed_hostnames or SecurityConfig().allowed_hostnames,
    )

    app = FastAPI(title="Templix", version="0.1.0", docs_url=None, redoc_url=None, openapi_url=None)
    engine = get_engine(f"sqlite:///{home / 'templix.db'}")
    home.mkdir(parents=True, exist_ok=True)
    init_db(engine)

    app.state.cfg = cfg
    app.state.engine = engine
    app.state.home = home
    app.state.blob = BlobStore(home / "blobs")
    app.state.jobs = default_runner()
    app.state.jobs.register("ingest", make_ingest_handler(engine, app.state.blob))
    app.state.vault = vault or KeyringStore()
    logger = configure_logging()

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        payload = exc.detail
        if isinstance(payload, dict) and "code" in payload:
            data = cast(dict[str, Any], payload)
            code: str | None = str(data["code"])
            hint = str(data.get("hint") or code)
        else:
            code = None
            hint = str(payload)
        return problem(
            exc.status_code,
            code=code,
            hint=hint,
            instance=request.url.path,
            headers=dict(exc.headers) if exc.headers else None,
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        return problem(
            422,
            code="invalid_request",
            hint="Check the request body and required fields.",
            detail="Request validation failed.",
            instance=request.url.path,
            errors=jsonable_encoder(exc.errors()),
        )

    @app.middleware("http")
    async def _security(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        bad = check_request(
            cfg,
            host=request.headers.get("host", ""),
            origin=request.headers.get("origin"),
            header_token=request.headers.get(HEADER),
            cookie_token=request.cookies.get(COOKIE),
        )
        is_bootstrap = (
            request.url.path == "/api/v1/session"
            and request.headers.get(LAUNCH_HEADER) == cfg.token
        )
        if bad == 401 and is_bootstrap:
            # Bootstrap: /session plants the session cookie, so it cannot require one yet.
            # The launch token matches here; the route verifies it again before setting it.
            bad = None
        if bad is not None:
            # Never log header values verbatim; the redaction filter is a second line of defence.
            logger.warning(
                "rejected %s %s status=%s host=%s origin=%s",
                request.method,
                request.url.path,
                bad,
                request.headers.get("host", ""),
                request.headers.get("origin"),
            )
            detail = "forbidden host" if bad == 403 else "missing or invalid session token"
            response: Response = problem(bad, hint=detail, instance=request.url.path)
        else:
            response = await call_next(request)
        for key, value in SECURITY_HEADERS.items():
            response.headers[key] = value
        return response

    from .routes import router

    # §11: all system endpoints are versioned under /api/v1 (M1 shipped them unprefixed).
    app.include_router(router)
    return app
