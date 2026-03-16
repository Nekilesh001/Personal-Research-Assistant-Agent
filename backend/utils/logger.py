"""
Structured logging configuration for the Personal Research Assistant Agent.

Uses structlog for structured, JSON-compatible log output with
timestamps, log levels, and request IDs.
"""

import os
import sys
import logging
from typing import Optional

import structlog
from dotenv import load_dotenv

load_dotenv()


def setup_logging() -> None:
    """
    Configure structlog and stdlib logging for the entire application.

    Reads LOG_LEVEL from environment (default: INFO).
    In development, outputs colored, human-readable logs.
    In production (ENVIRONMENT=production), outputs JSON.
    """
    log_level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_name, logging.INFO)
    environment = os.getenv("ENVIRONMENT", "development").lower()

    # Configure stdlib logging (used by uvicorn, httpx, etc.)
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    # Shared processors for all environments
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if environment == "production":
        # JSON output for production log aggregation
        renderer = structlog.processors.JSONRenderer()
    else:
        # Colored, padded output for development readability
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Apply structlog formatting to the root handler
    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    root_logger = logging.getLogger()
    if root_logger.handlers:
        for handler in root_logger.handlers:
            handler.setFormatter(formatter)
    else:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)

    root_logger.setLevel(log_level)

    # Quiet down noisy third-party loggers
    for noisy_logger in ["httpx", "chromadb", "urllib3", "httpcore"]:
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)


def get_logger(name: Optional[str] = None) -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger instance.

    Args:
        name: Logger name (typically __name__ from the calling module).

    Returns:
        A bound structlog logger with structured output.
    """
    return structlog.get_logger(name or __name__)


# Initialize logging on module import
setup_logging()
