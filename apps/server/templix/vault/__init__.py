"""Credential vault: provider API keys live in the OS keyring, never in the DB or logs (§10.3).

`SecretStore` is the small surface the API talks to. `KeyringStore` is the real OS-backed backend;
`MemoryStore` is used by tests and headless runs so nothing ever writes a real credential.
"""

from __future__ import annotations

import contextlib
from typing import Protocol

import keyring
from keyring.errors import PasswordDeleteError

SERVICE = "templix"


class SecretStore(Protocol):
    def get(self, provider: str) -> str | None: ...

    def set(self, provider: str, key: str) -> None: ...

    def delete(self, provider: str) -> None: ...


class KeyringStore:
    """Persist secrets in the OS keyring (Windows Credential Locker, macOS Keychain, …)."""

    def get(self, provider: str) -> str | None:
        return keyring.get_password(SERVICE, provider)

    def set(self, provider: str, key: str) -> None:
        keyring.set_password(SERVICE, provider, key)

    def delete(self, provider: str) -> None:
        # deletion is idempotent: a missing key is not an error
        with contextlib.suppress(PasswordDeleteError):
            keyring.delete_password(SERVICE, provider)


class MemoryStore:
    """In-memory store: deterministic, no OS keyring, never outlives the process."""

    def __init__(self) -> None:
        self._data: dict[str, str] = {}

    def get(self, provider: str) -> str | None:
        return self._data.get(provider)

    def set(self, provider: str, key: str) -> None:
        self._data[provider] = key

    def delete(self, provider: str) -> None:
        self._data.pop(provider, None)
