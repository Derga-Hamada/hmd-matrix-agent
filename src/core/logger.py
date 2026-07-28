"""
Structured Logging Infrastructure.

Provides formatted logging standard across synchronous and asynchronous contexts.
"""

import sys
import logging
from src.config.settings import settings


def setup_logger(name: str = "hmd_matrix") -> logging.Logger:
    """Configures and returns a context-aware logger instance."""
    logger = logging.getLogger(name)

    # Avoid duplicate handler registration
    if logger.handlers:
        return logger

    log_level = logging.DEBUG if settings.DEBUG else logging.INFO
    logger.setLevel(log_level)

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        fmt="[%(asctime)s] [%(levelname)s] [%(name)s:%(filename)s:%(lineno)d]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


# Global engine logger
logger = setup_logger()