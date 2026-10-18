"""Redaction tests (NFR-SEC-03): key-shaped secrets never survive into a log record."""

from __future__ import annotations

import json
import logging

from _pytest.logging import LogCaptureFixture
from fastapi.testclient import TestClient

from templix.api.logging import JsonFormatter, RedactingFilter, redact


def test_redacts_key_value_shapes() -> None:
    msg = "connect password=hunter2 api_key=sk_live_51AbCdEfGh123456 session=deadbeefcafe"
    out = redact(msg)
    assert "hunter2" not in out
    assert "sk_live_51AbCdEfGh123456" not in out
    assert "deadbeefcafe" not in out
    assert out.count("[REDACTED]") >= 3
    assert "connect" in out  # non-secret text is preserved


def test_redacts_bearer_and_prefixed_keys() -> None:
    assert "eyJhbGciOiJIUzI1NiJ9" not in redact("Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.payload")
    assert "solo_abcdef123456" not in redact("got tok_abcdef123456 in body")


def test_filter_scrubs_emitted_records(caplog: LogCaptureFixture) -> None:
    logger = logging.getLogger("templix.test.redaction")
    logger.setLevel(logging.INFO)
    logger.addFilter(RedactingFilter())
    with caplog.at_level(logging.INFO):
        logger.info("auth token=%s", "super-secret-value")
    assert "super-secret-value" not in caplog.text
    assert "[REDACTED]" in caplog.text


def test_json_formatter_emits_structured_redacted_line() -> None:
    record = logging.LogRecord(
        "templix.api",
        logging.WARNING,
        __file__,
        1,
        "api_key=sk_live_51AbCdEfGh123456 for openai",
        None,
        None,
    )
    line = JsonFormatter().format(record)
    payload = json.loads(line)  # structured: one parseable JSON object per line
    assert payload["level"] == "WARNING"
    assert payload["logger"] == "templix.api"
    assert "sk_live_51AbCdEfGh123456" not in line  # redacted even without the filter attached
    assert "[REDACTED]" in payload["msg"]
    assert "for openai" in payload["msg"]  # non-secret text is preserved


def test_app_wires_structured_logging(client: TestClient) -> None:
    assert client.get("/api/v1/status").status_code == 200  # app factory ran configure_logging()
    logger = logging.getLogger("templix.api")
    assert any(isinstance(getattr(h, "formatter", None), JsonFormatter) for h in logger.handlers)
    assert logger.propagate is False  # no duplicate plain-format output via root/uvicorn
