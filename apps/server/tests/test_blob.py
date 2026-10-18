"""Blob store tests (NFR-REL-02): content-addressed, idempotent, sharded, atomic."""

from __future__ import annotations

import hashlib
from pathlib import Path

from templix.store.blob import BlobStore


def test_put_returns_sha256_and_round_trips(tmp_path: Path) -> None:
    store = BlobStore(tmp_path / "blobs")
    data = b"hello templix"
    digest = store.put(data)
    assert digest == hashlib.sha256(data).hexdigest()
    assert store.get(digest) == data
    assert store.exists(digest)
    assert store.path(digest).parent.name == digest[:2]  # sharded <root>/<sha[:2]>/<sha>


def test_put_is_idempotent(tmp_path: Path) -> None:
    store = BlobStore(tmp_path / "blobs")
    data = b"same bytes"
    assert store.put(data) == store.put(data)
    files = [p for p in (tmp_path / "blobs").rglob("*") if p.is_file()]
    assert len(files) == 1  # one content-addressed blob, no leftover temp files


def test_get_missing_returns_none(tmp_path: Path) -> None:
    store = BlobStore(tmp_path / "blobs")
    missing = "0" * 64
    assert store.get(missing) is None
    assert not store.exists(missing)
