"""Shared pytest fixtures for the lonis test suite."""

from pathlib import Path

import pytest


@pytest.fixture
def datadir() -> Path:
    """Path to tests/data."""
    return Path(__file__).parent / "data"
