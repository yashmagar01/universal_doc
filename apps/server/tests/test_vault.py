"""Vault + provider config tests: write-only keys (NFR-SEC-03) and the offline FakeProvider."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from templix.provider import FakeProvider
from templix.vault import MemoryStore

FULL_KEY = "sk-live-51AbCdEfGh1234"


def test_memory_store_roundtrip() -> None:
    store = MemoryStore()
    assert store.get("openai") is None
    store.set("openai", FULL_KEY)
    assert store.get("openai") == FULL_KEY
    store.delete("openai")
    assert store.get("openai") is None
    store.delete("openai")  # idempotent


def test_provider_key_is_write_only(client: TestClient) -> None:
    set_r = client.put("/api/v1/providers/fake/key", json={"key": FULL_KEY})
    assert set_r.status_code == 200
    assert set_r.json() == {"provider": "fake", "configured": True}  # key never echoed back
    assert FULL_KEY not in set_r.text

    got = client.get("/api/v1/providers/fake")
    assert got.status_code == 200
    body = got.json()
    assert body["configured"] is True
    assert str(body["hint"]).endswith("1234")  # only a masked tail leaves the server
    assert FULL_KEY not in got.text

    gone = client.delete("/api/v1/providers/fake/key")
    assert gone.json()["configured"] is False
    assert client.get("/api/v1/providers/fake").json()["configured"] is False


def test_provider_unconfigured_has_no_hint(client: TestClient) -> None:
    assert client.get("/api/v1/providers/nope").json() == {
        "provider": "nope",
        "configured": False,
        "hint": None,
    }


def test_provider_rejects_empty_key(client: TestClient) -> None:
    assert client.put("/api/v1/providers/fake/key", json={"key": ""}).status_code == 422


def test_fake_provider_reads_vault_and_is_offline() -> None:
    store = MemoryStore()
    prov = FakeProvider(store)
    assert not prov.is_ready()
    with pytest.raises(RuntimeError, match="no api key"):
        prov.complete("hi")

    store.set("fake", "sk-test-9999")
    assert prov.is_ready()
    assert prov.complete("hi") == "fake:hi"  # deterministic, no network
    assert prov.complete("hi") == prov.complete("hi")
