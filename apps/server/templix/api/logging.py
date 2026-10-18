"""Log redaction (NFR-SEC-03): secrets never reach the log file.

`redact()` scrubs three shapes of secret:
- ``key=value`` / ``key: value`` where the key is credential-shaped (token, password, …),
- ``Bearer …`` / ``Basic …`` authorization values,
- prefixed API keys (``sk_``, ``tok_``, …).

Attach :class:`RedactingFilter` to any logger whose records must be safe to store.
"""

from __future__ import annotations

import json
import logging
import re

_REDACTED = "[REDACTED]"

_SECRET_KEY = (
    r"token|secret|password|passwd|pwd|api[_-]?key|access[_-]?key|"
    r"authorization|auth|bearer|session|cookie|credential"
)
_KEYVAL = re.compile(rf"(?i)(\b(?:{_SECRET_KEY})\b\s*[=:]\s*)([^\s,;]+)")
_AUTH = re.compile(r"(?i)\b(bearer|basic)\s+([A-Za-z0-9\-._~+/]+=*)")
_APIKEY = re.compile(r"\b(?:sk|pk|rk|tok)(?:_[A-Za-z0-9]+)+\b")


def redact(text: str) -> str:
    """Return `text` with credential-shaped values replaced by ``[REDACTED]``."""
    # `_AUTH` must run first: for `Authorization: Bearer <tok>` the key/value pass would
    # otherwise only consume the word `Bearer` and leave the token itself in the clear.
    out = _AUTH.sub(rf"\1 {_REDACTED}", text)
    out = _KEYVAL.sub(rf"\1{_REDACTED}", out)
    return _APIKEY.sub(_REDACTED, out)


class RedactingFilter(logging.Filter):
    """Rewrites each record's formatted message in place, so stored logs carry no secrets."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = redact(record.getMessage())
        record.args = ()
        return True


class JsonFormatter(logging.Formatter):
    """One JSON object per line: machine-parseable (structured) and secret-free (NFR-SEC-03).

    Redaction runs here as well as in :class:`RedactingFilter` — `redact()` is idempotent, and this
    guarantees a safe line even if the formatter is attached to a logger without the filter.
    """

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "msg": redact(record.getMessage()),
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(logger_name: str = "templix.api", level: int = logging.INFO) -> logging.Logger:
    """Attach a structured, redacting JSON handler to the app logger (idempotent)."""
    logger = attach_redaction(logger_name)
    if not any(isinstance(getattr(h, "formatter", None), JsonFormatter) for h in logger.handlers):
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
    # Emit only through the structured handler, not again via root/uvicorn's plain formatter.
    logger.propagate = False
    logger.setLevel(level)
    return logger


def attach_redaction(logger_name: str = "templix") -> logging.Logger:
    logger = logging.getLogger(logger_name)
    if not any(isinstance(f, RedactingFilter) for f in logger.filters):
        logger.addFilter(RedactingFilter())
    return logger
