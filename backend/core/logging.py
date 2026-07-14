"""
Structured logging configuration.

Provides a configured logger factory. All modules use get_logger(__name__)
instead of raw print() or logging.getLogger().
"""

import logging
import sys
from typing import Optional

from core.config import get_settings


_configured = False


def _configure_logging() -> None:
    """Configure root logger with structured format. Called once."""
    global _configured
    if _configured:
        return

    settings = get_settings()
    level = getattr(logging, settings.app_log_level.upper(), logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.setLevel(level)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers.clear()
    root_logger.addHandler(handler)

    # Quieten noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    _configured = True


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a configured logger instance.

    Args:
        name: Logger name (typically __name__).

    Returns:
        Configured Logger instance.
    """
    _configure_logging()
    return logging.getLogger(name or "mskai")
