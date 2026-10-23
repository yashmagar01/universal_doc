"""Request-authenticity tests: DNS rebinding (Host), CSRF (Origin), session token (NFR-SEC-02)."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from templix.api import SecurityConfig, check_request
from templix.api.security import HEADER, LAUNCH_HEADER
from tests.conftest import TOKEN


def test_dns_rebinding_bad_host_rejected(app: FastAPI) -> None:
    # A rebound domain reaches the local server but sends Host: evil.com — must be refused.
    evil = TestClient(app, base_url="http://evil.com", headers={HEADER: TOKEN})
    assert evil.get("/api/v1/status").status_code == 403


def test_csrf_cross_site_origin_rejected(client: TestClient) -> None:
    assert client.get("/api/v1/status", headers={"Origin": "https://evil.com"}).status_code == 403
    assert client.get("/api/v1/status", headers={"Origin": "null"}).status_code == 403
    assert client.get("/api/v1/status", headers={"Origin": "http://localhost:8000"}).status_code == 200


def test_missing_or_wrong_token_401(client: TestClient) -> None:
    assert client.get("/api/v1/status", headers={HEADER: "wrong"}).status_code == 401
    assert client.get("/api/v1/status", headers={HEADER: ""}).status_code == 401


def test_check_request_matrix() -> None:
    cfg = SecurityConfig(token="T")

    assert check_request(cfg, host="localhost:8000", origin=None, header_token="T", cookie_token=None) is None
    assert check_request(cfg, host="localhost:8000", origin=None, header_token=None, cookie_token="T") is None

    assert check_request(cfg, host="evil.com", origin=None, header_token="T", cookie_token=None) == 403
    assert check_request(
        cfg, host="localhost:8000", origin="https://evil.com", header_token="T", cookie_token=None
    ) == 403
    assert check_request(cfg, host="127.0.0.1:8765", origin=None, header_token="T", cookie_token=None) is None
    assert check_request(cfg, host="localhost:8000", origin=None, header_token=None, cookie_token=None) == 401


def test_launch_token_required_for_session(client: TestClient) -> None:
    # Override the default (valid) token header so only the bogus launch token is presented.
    assert client.post("/api/v1/session", headers={LAUNCH_HEADER: "nope", HEADER: ""}).status_code == 401
    assert client.post("/api/v1/session", headers={HEADER: ""}).status_code == 401


def test_session_bootstraps_cookie_without_existing_session(app: FastAPI) -> None:
    # The one-time URL is the only credential at bootstrap: no header and no cookie yet.
    fresh = TestClient(app, base_url="http://localhost:8000")
    r = fresh.post("/api/v1/session", headers={LAUNCH_HEADER: TOKEN})
    assert r.status_code == 200
    assert "templix_session" in r.cookies
    # the planted SameSite=Strict cookie alone now authenticates every endpoint
    assert fresh.get("/api/v1/templates").status_code == 200
