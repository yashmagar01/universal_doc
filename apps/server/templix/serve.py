"""Local server entry: `uv run python -m templix.serve` (NFR-SEC-02, §10.2).

Binds 127.0.0.1 only, mints a per-launch session token (or reuses TEMPLIX_TOKEN for dev/e2e)
and prints the one-time URL the browser opens to establish its SameSite=Strict cookie.
State lives under TEMPLIX_HOME (default ~/.templix).
"""

from __future__ import annotations

import os
from pathlib import Path

import uvicorn

from .api import create_app
from .api.security import generate_token


def main() -> None:
    home = Path(os.environ.get("TEMPLIX_HOME", str(Path.home() / ".templix")))
    token = os.environ.get("TEMPLIX_TOKEN") or generate_token()
    port = int(os.environ.get("TEMPLIX_PORT", "8000"))
    web_port = int(os.environ.get("TEMPLIX_WEB_PORT", "5173"))
    app = create_app(home, token=token)
    print(f"Templix home:  {home}")
    print(f"One-time URL:  http://localhost:{web_port}/?token={token}")
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")


if __name__ == "__main__":
    main()
