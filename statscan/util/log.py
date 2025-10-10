"""Logging configuration utilities for the Statistics Canada package.

This module provides helper functions to configure Python's logging system
with consistent formatting and level management.
"""
import logging


def configure_logging(
    fmt: str = (
        "%(asctime)s :: %(levelname)s :: %(name)s :: "
        "%(module)s.%(funcName)s:%(lineno)d - %(message)s"
    ),
    level: int | str | None = None,
):
    """Configure the root logger with a consistent format and level.

    Args:
        fmt: The log message format string.
        level: The logging level (can be an int or level name string).

    """
    if isinstance(level, str):
        level = logging.getLevelNamesMapping()[level.upper()]
    logging.basicConfig(format=fmt, level=level)
