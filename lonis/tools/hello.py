"""Placeholder tool demonstrating the defopt CLI pattern."""

import logging

logger = logging.getLogger(__name__)


def hello(*, name: str = "world") -> None:
    """
    Print a greeting.

    Args:
        name: The name to greet.
    """
    logger.info(f"Hello, {name}!")
