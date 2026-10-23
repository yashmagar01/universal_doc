"""Font resolution cascade (D-018, FR-ING-11).

PDF font name -> `FontResolution{requested, resolved, source, certainty}`:
subset prefix stripped, style suffix split off, then: bundled exact match
(1.0) -> system exact match (1.0) -> metric-compatible alias (0.5, warn) ->
fuzzy family match, score >= 90 (0.4) -> unresolved (0.0, error).

# ponytail: the index is a short static list (bundled Inter + common system families); the font
# manager (M4) replaces it with bundled files + user uploads + the consent-gated Google cache.
# Weight/style only picks the family here - style files are not indexed yet.
"""

from __future__ import annotations

import re

from rapidfuzz import process as fuzz_process

from ..model import FontResolution, FontSource

_SUBSET_RE = re.compile(r"^[A-Z]{6}\+")

# family key (lowercase alphanumeric) -> canonical family name
_BUNDLED: dict[str, str] = {"inter": "Inter", "intervariable": "Inter"}
_SYSTEM: dict[str, str] = {
    "arial": "Arial",
    "timesnewroman": "Times New Roman",
    "couriernew": "Courier New",
    "georgia": "Georgia",
    "verdana": "Verdana",
    "tahoma": "Tahoma",
    "trebuchetms": "Trebuchet MS",
    "segoeui": "Segoe UI",
    "calibri": "Calibri",
}
# metric-compatible substitutes for the base-14 families we do not ship (D-018 step 4)
_ALIASES: dict[str, str] = {
    "helvetica": "arial",
    "times": "timesnewroman",
    "courier": "couriernew",
}

_ITALIC = {"italic", "oblique", "ital"}
_STYLES: dict[str, int] = {
    "extralight": 200,
    "ultralight": 200,
    "extrabold": 800,
    "ultrabold": 800,
    "semibold": 600,
    "demibold": 600,
    "bold": 700,
    "medium": 500,
    "black": 900,
    "heavy": 900,
    "light": 300,
    "thin": 100,
    "hairline": 100,
    "book": 400,
    "regular": 400,
    "normal": 400,
    "roman": 400,
    "italic": 400,
    "oblique": 400,
    "ital": 400,
}
_TRAILING = ("psmt", "mt", "ps")  # glued bits like ArialMT / TimesNewRomanPSMT


def _clean(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower())


def _strip_trailing(key: str) -> str:
    for suffix in _TRAILING:
        if len(key) > len(suffix) + 2 and key.endswith(suffix):
            return key[: -len(suffix)]
    return key


def _consume_styles(low: str) -> tuple[int, bool] | None:
    """Consume the token entirely as style words (`bolditalic` -> 700, italic); None otherwise."""
    rest = low
    weight = 400
    italic = False
    while rest:
        for word, value in sorted(_STYLES.items(), key=lambda kv: -len(kv[0])):
            if rest.endswith(word):
                rest = rest[: -len(word)]
                weight = value
                italic = italic or word in _ITALIC
                break
        else:
            return None
    return weight, italic


def _split_style(name: str) -> tuple[str, int, bool]:
    """`Helvetica-BoldOblique` -> (`helvetica`, 700, True).

    A token is only treated as style words when it is *entirely* style words, so
    `TimesNewRoman` stays one family token instead of losing its `Roman`."""
    weight = 400
    italic = False
    family: list[str] = []
    for token in re.split(r"[-_,\s]+", name):
        low = token.lower()
        if not low:
            continue
        if low in _STYLES:
            weight = _STYLES[low]
            italic = italic or low in _ITALIC
            continue
        consumed = _consume_styles(low)
        if consumed is not None:
            weight, italic = consumed
            continue
        family.append(low)
    return _clean("".join(family)), weight, italic


def _lookup(key: str, requested: str, *, certainty: float = 1.0) -> FontResolution | None:
    if key in _BUNDLED:
        return FontResolution(
            requested=requested, resolved=_BUNDLED[key], source=FontSource.local, certainty=certainty
        )
    if key in _SYSTEM:
        return FontResolution(
            requested=requested,
            resolved=_SYSTEM[key],
            source=FontSource.system,
            certainty=certainty,
        )
    if key in _ALIASES:
        return FontResolution(
            requested=requested,
            resolved=_SYSTEM[_ALIASES[key]],
            source=FontSource.system,
            certainty=min(certainty, 0.5),
        )
    return None


def resolve(name: str) -> FontResolution:
    """Resolve one PDF font name through the D-018 cascade."""
    cleaned = _SUBSET_RE.sub("", name.strip())
    key = _clean(cleaned)
    for candidate in (key, _strip_trailing(key)):
        hit = _lookup(candidate, name)
        if hit is not None:
            return hit
    family, _weight, _italic = _split_style(cleaned)
    for candidate in (family, _strip_trailing(family)):
        hit = _lookup(candidate, name)
        if hit is not None:
            return hit
    match = fuzz_process.extractOne(
        family, list(_BUNDLED) + list(_SYSTEM) + list(_ALIASES), score_cutoff=90
    )
    if match is not None and family:
        hit = _lookup(str(match[0]), name, certainty=0.4)
        if hit is not None:
            return hit
    return FontResolution(requested=name, resolved=None, source=None, certainty=0.0)


def resolve_names(names: list[str]) -> dict[str, FontResolution]:
    """Resolve a batch, one entry per distinct requested name."""
    return {name: resolve(name) for name in dict.fromkeys(names)}


def family_of(name: str) -> str:
    """Human family name for an unresolved font: style tokens dropped, original casing kept.

    `ZzTopFont-Heavy` -> `ZzTopFont`; used for tokens/review text, not for rendering."""
    cleaned = _SUBSET_RE.sub("", name.strip())
    tokens = [token for token in re.split(r"[-_,\s]+", cleaned) if token]
    family = [token for token in tokens if _consume_styles(_clean(token)) is None]
    return " ".join(family) if family else (cleaned or name)
