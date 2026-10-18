"""FastAPI application factory: security middleware, status, session (§11, §10.2)."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse

from ..model import SCHEMA_VERSION
from ..store import get_engine, init_db
from ..vault import KeyringStore, SecretStore
from .jobs import default_runner
from .logging import configure_logging
from .security import COOKIE, HEADER, LAUNCH_HEADER, SECURITY_HEADERS, SecurityConfig, check_request


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
    app.state.jobs = default_runner()
    app.state.vault = vault or KeyringStore()
    logger = configure_logging()

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
            response: Response = JSONResponse({"detail": detail}, status_code=bad)
        else:
            response = await call_next(request)
        for key, value in SECURITY_HEADERS.items():
            response.headers[key] = value
        return response

    @app.get("/status")
    def status() -> dict[str, object]:
        return {"schemaVersion": SCHEMA_VERSION, "state": "ok"}

    @app.post("/session")
    def session(request: Request, response: Response) -> dict[str, str]:
        # Launch token == session token; this sets the SameSite=Strict cookie for browser flows.
        if request.headers.get(LAUNCH_HEADER) != cfg.token and request.headers.get(HEADER) != cfg.token:
            raise HTTPException(401, "invalid launch token")
        response.set_cookie(COOKIE, cfg.token, samesite="strict", httponly=True, path="/")
        return {"token": cfg.token}

    from .routes import router

    app.include_router(router)
    return app
