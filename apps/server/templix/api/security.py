"""Request authenticity: session token, Host/Origin allowlist, security headers (§10.2, NFR-SEC-02).

Defends the local API against DNS rebinding and CSRF:

- **Host allowlist** — a rebinding attacker's `Host: evil.com` is rejected (403).
- **Origin allowlist** — cross-site state-changing requests (`Origin: https://evil.com`) rejected (403).
- **Session token** — a per-launch random token required on every request via `X-Templix-Token`
  header or the `SameSite=Strict` session cookie (401 without it). No permissive CORS, so a browser
  on another origin can never read or attach the token.
- **Security headers** on every response.

The validation is a pure function (`check_request`) so the security tests can exercise it directly.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from secrets import token_urlsafe
from urllib.parse import urlparse

HEADER = "X-Templix-Token"
LAUNCH_HEADER = "X-Templix-Launch-Token"
COOKIE = "templix_session"

DEFAULT_HOSTNAMES = frozenset({"localhost", "127.0.0.1", "::1", "[::1]"})

SECURITY_HEADERS = {
    "x-content-type-options": "nosniff",
    "x-frame-options": "DENY",
    "referrer-policy": "no-referrer",
    "cross-origin-opener-policy": "same-origin",
    "cross-origin-resource-policy": "same-origin",
    "content-security-policy": "default-src 'self'",
}


def generate_token() -> str:
    return token_urlsafe(32)


@dataclass(frozen=True)
class SecurityConfig:
    token: str = field(default_factory=generate_token)
    allowed_hostnames: frozenset[str] = DEFAULT_HOSTNAMES


def _hostname(host_header: str) -> str:
    """Hostname portion of a Host header, port stripped (handles `127.0.0.1:8000`)."""
    raw = host_header.strip().lower()
    if raw.startswith("["):  # IPv6 literal [::1]:8000
        end = raw.find("]")
        return raw[: end + 1] if end != -1 else raw
    return raw.split(":")[0]


def check_request(
    cfg: SecurityConfig,
    *,
    host: str,
    origin: str | None,
    header_token: str | None,
    cookie_token: str | None,
) -> int | None:
    """Return an HTTP error status if the request must be rejected, else None."""
    if _hostname(host) not in cfg.allowed_hostnames:
        return 403  # DNS rebinding / wrong Host

    if origin:
        parsed = urlparse(origin)
        # `null` origin (sandboxed/file) and foreign origins are both rejected
        if not parsed.hostname or parsed.hostname not in cfg.allowed_hostnames:
            return 403  # cross-site (CSRF)

    if header_token != cfg.token and cookie_token != cfg.token:
        return 401  # missing/invalid session token

    return None


def hostname_allowed(hostnames: Iterable[str]) -> frozenset[str]:
    return frozenset(h.strip().lower() for h in hostnames)
