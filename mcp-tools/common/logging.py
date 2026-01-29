"""
Logging configuration for MCP tools.
Provides consistent logging across all servers.
"""

import logging
import sys
from typing import Optional

from .config import config

def get_logger(name: str, level: Optional[int] = None) -> logging.Logger:
    """
    Get a configured logger instance.

    Args:
        name: Logger name
        level: Optional override for log level

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Only configure if no handlers exist (avoid duplicate handlers)
    if not logger.handlers:
        # Set level based on debug mode or override
        if level is not None:
            logger.setLevel(level)
        elif config.debug:
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.INFO)

        # Create console handler
        handler = logging.StreamHandler(stream=sys.stdout)
        handler.setLevel(logging.DEBUG)

        # Create formatter
        formatter = logging.Formatter(
            fmt="%(asctime)s \t| %(name)s \t| %(levelname)s \t| %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)

        # Add handler to logger
        logger.addHandler(handler)

    return logger