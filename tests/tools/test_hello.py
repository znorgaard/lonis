"""Tests for the hello tool."""

import logging

import pytest

from lonis.tools.hello import hello


def test_hello_default(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.INFO, logger="lonis.tools.hello"):
        hello()
    assert "Hello, world!" in caplog.text


def test_hello_custom_name(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.INFO, logger="lonis.tools.hello"):
        hello(name="Lonis")
    assert "Hello, Lonis!" in caplog.text
