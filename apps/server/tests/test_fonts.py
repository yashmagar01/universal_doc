"""Font resolution cascade (FR-ING-11, D-018)."""

from __future__ import annotations

import pytest

from templix.ingest.fonts import resolve, resolve_names
from templix.model import FontSource


@pytest.mark.parametrize(
    ("name", "family", "source", "certainty"),
    [
        ("Inter", "Inter", FontSource.local, 1.0),
        ("Inter-SemiBold", "Inter", FontSource.local, 1.0),
        ("InterVariable", "Inter", FontSource.local, 1.0),
        ("Georgia", "Georgia", FontSource.system, 1.0),
        ("Calibri-Bold", "Calibri", FontSource.system, 1.0),
        ("ABCDEF+ArialMT", "Arial", FontSource.system, 1.0),
        ("Arial Black", "Arial", FontSource.system, 1.0),
        ("TimesNewRomanPSMT", "Times New Roman", FontSource.system, 1.0),
        ("TimesNewRoman-Bold", "Times New Roman", FontSource.system, 1.0),
        ("Helvetica", "Arial", FontSource.system, 0.5),
        ("Helvetica-BoldOblique", "Arial", FontSource.system, 0.5),
        ("Times-Roman", "Times New Roman", FontSource.system, 0.5),
        ("Courier", "Courier New", FontSource.system, 0.5),
        ("Gorgia", "Georgia", FontSource.system, 0.4),
    ],
)
def test_cascade(name: str, family: str, source: FontSource, certainty: float) -> None:
    result = resolve(name)
    assert result.requested == name
    assert result.resolved == family
    assert result.source is source
    assert result.certainty == certainty


def test_unresolved_is_none_with_zero_certainty() -> None:
    result = resolve("ZzTopFont-Heavy")
    assert result.resolved is None
    assert result.source is None
    assert result.certainty == 0.0


def test_resolve_names_dedupes() -> None:
    resolved = resolve_names(["Helvetica", "Helvetica", "Inter"])
    assert list(resolved) == ["Helvetica", "Inter"]
