"""Shared fixtures: an app on a temp home with a known token (M1 acceptance harness)."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from templix.api import create_app
from templix.vault import MemoryStore

TOKEN = "test-token-123"


@pytest.fixture
def home(tmp_path: Path) -> Path:
    return tmp_path / "home"


@pytest.fixture
def app(home: Path) -> FastAPI:
    # MemoryStore keeps tests off the real OS keyring (no credential is ever written).
    return create_app(home, token=TOKEN, vault=MemoryStore())


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    with TestClient(app, base_url="http://localhost:8000", headers={"X-Templix-Token": TOKEN}) as c:
        yield c
