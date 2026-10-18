"""Provider adapters (§9). M1 ships only the no-network `FakeProvider` every test uses."""

from __future__ import annotations

from ..vault import SecretStore


class FakeProvider:
    """Deterministic, offline provider: proves the vault→provider path without any network."""

    name = "fake"

    def __init__(self, store: SecretStore, name: str = "fake") -> None:
        self._store = store
        self._name = name

    @property
    def key(self) -> str | None:
        return self._store.get(self._name)

    def is_ready(self) -> bool:
        return bool(self.key)

    def complete(self, prompt: str) -> str:
        if not self.is_ready():
            raise RuntimeError(f"provider {self._name} has no api key configured")
        return f"fake:{prompt}"
