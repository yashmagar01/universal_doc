"""Content-addressed blob store (architecture §10.4, NFR-REL-02).

Large files live under `<home>/blobs/<sha256[:2]>/<sha256>`, written atomically via temp+rename
so a crash mid-write never leaves a partial blob. DB only stores the digest + metadata.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path


class BlobStore:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _path_for(self, digest: str) -> Path:
        return self.root / digest[:2] / digest

    def put(self, data: bytes) -> str:
        """Store bytes; return sha256. Idempotent. Atomic (temp + os.replace)."""
        digest = hashlib.sha256(data).hexdigest()
        target = self._path_for(digest)
        if target.exists():
            return digest
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_suffix(f".tmp{os.getpid()}")
        tmp.write_bytes(data)
        os.replace(tmp, target)  # atomic on the same filesystem
        return digest

    def get(self, digest: str) -> bytes | None:
        p = self._path_for(digest)
        return p.read_bytes() if p.exists() else None

    def path(self, digest: str) -> Path:
        return self._path_for(digest)

    def exists(self, digest: str) -> bool:
        return self._path_for(digest).exists()
