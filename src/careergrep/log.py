"""Structured JSON logging for careergrep.

Python's logging module works similarly to Monolog in PHP: you configure
handlers and formatters once at startup, then use module-level loggers
everywhere else. The JSON formatter makes logs grep-friendly and easy
to pipe into tools like jq.
"""

import json
import logging
import sys
from datetime import datetime, timezone


class JsonFormatter(logging.Formatter):
    """Emit each log record as a single JSON line."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        # Attach any extra fields passed via logger.info("...", extra={...})
        for key, val in record.__dict__.items():
            if key not in logging.LogRecord.__dict__ and not key.startswith("_"):
                payload[key] = val

        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)

        return json.dumps(payload)


def setup_logging(level: int = logging.INFO, json: bool = True) -> None:
    """Configure root logger. Call once at process startup (CLI or API)."""
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(JsonFormatter() if json else logging.Formatter(
        "%(asctime)s %(levelname)-8s %(name)s — %(message)s"
    ))
    root = logging.getLogger()
    root.setLevel(level)
    # Avoid adding duplicate handlers if called more than once
    root.handlers.clear()
    root.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """Return a module-level logger. Usage: logger = get_logger(__name__)"""
    return logging.getLogger(name)
