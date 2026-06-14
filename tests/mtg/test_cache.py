"""Tests for MtgDataCache."""

import io
import json
import os
import time
from pathlib import Path
from typing import Any

import pytest
from pytest_mock import MockerFixture

import lonis.mtg.cache
from lonis.mtg.cache import MtgDataCache

_SAMPLE_DATA: dict[str, Any] = {
    "data": {
        "Elvish Mystic": [
            {
                "layout": "normal",
                "types": ["Creature"],
                "subtypes": ["Elf", "Druid"],
                "supertypes": [],
                "legalities": {"commander": "Legal"},
                "isFunny": False,
            }
        ],
    }
}

_UPDATED_DATA: dict[str, Any] = {
    "data": {
        "Goblin Guide": [
            {
                "layout": "normal",
                "types": ["Creature"],
                "subtypes": ["Goblin", "Scout"],
                "supertypes": [],
                "legalities": {"commander": "Legal"},
                "isFunny": False,
            }
        ],
    }
}


def _write_cache(cache_file: Path, data: dict[str, Any]) -> None:
    cache_file.write_text(json.dumps(data))


def _set_mtime_yesterday(path: Path) -> None:
    yesterday = time.time() - 86401
    os.utime(path, (yesterday, yesterday))


def test_load_uses_cache_when_fresh(tmp_path: Path, mocker: MockerFixture) -> None:
    cache_file = tmp_path / "AtomicCards.json"
    _write_cache(cache_file, _SAMPLE_DATA)
    mock_open = mocker.patch.object(lonis.mtg.cache._opener, "open")
    cache = MtgDataCache(cache_dir=tmp_path)
    result = cache.load()
    mock_open.assert_not_called()
    assert "Elvish Mystic" in result


def test_load_redownloads_when_stale(tmp_path: Path, mocker: MockerFixture) -> None:
    cache_file = tmp_path / "AtomicCards.json"
    _write_cache(cache_file, _SAMPLE_DATA)
    _set_mtime_yesterday(cache_file)

    response_body = json.dumps(_UPDATED_DATA).encode()
    mock_response = mocker.MagicMock()
    mock_response.__enter__ = mocker.Mock(return_value=io.BytesIO(response_body))
    mock_response.__exit__ = mocker.Mock(return_value=False)
    mocker.patch.object(lonis.mtg.cache._opener, "open", return_value=mock_response)
    cache = MtgDataCache(cache_dir=tmp_path)
    result = cache.load()
    assert "Goblin Guide" in result
    assert "Elvish Mystic" not in result


def test_load_downloads_when_missing(tmp_path: Path, mocker: MockerFixture) -> None:
    response_body = json.dumps(_SAMPLE_DATA).encode()
    mock_response = mocker.MagicMock()
    mock_response.__enter__ = mocker.Mock(return_value=io.BytesIO(response_body))
    mock_response.__exit__ = mocker.Mock(return_value=False)
    mock_open = mocker.patch.object(lonis.mtg.cache._opener, "open", return_value=mock_response)
    cache = MtgDataCache(cache_dir=tmp_path)
    result = cache.load()
    mock_open.assert_called_once()
    assert "Elvish Mystic" in result


def test_load_redownloads_corrupt_cache(tmp_path: Path, mocker: MockerFixture) -> None:
    cache_file = tmp_path / "AtomicCards.json"
    cache_file.write_text("this is not valid json {{{")

    response_body = json.dumps(_SAMPLE_DATA).encode()
    mock_response = mocker.MagicMock()
    mock_response.__enter__ = mocker.Mock(return_value=io.BytesIO(response_body))
    mock_response.__exit__ = mocker.Mock(return_value=False)
    mock_open = mocker.patch.object(lonis.mtg.cache._opener, "open", return_value=mock_response)
    cache = MtgDataCache(cache_dir=tmp_path)
    result = cache.load()
    mock_open.assert_called_once()
    assert "Elvish Mystic" in result


def test_load_raises_on_download_failure(tmp_path: Path, mocker: MockerFixture) -> None:
    mocker.patch.object(lonis.mtg.cache._opener, "open", side_effect=OSError("connection refused"))
    cache = MtgDataCache(cache_dir=tmp_path)
    with pytest.raises(RuntimeError, match="Failed to download"):
        cache.load()


def test_load_raises_when_redownload_still_corrupt(tmp_path: Path, mocker: MockerFixture) -> None:
    cache_file = tmp_path / "AtomicCards.json"
    cache_file.write_text("first corrupt content")

    response_body = b"second corrupt content"
    mock_response = mocker.MagicMock()
    mock_response.__enter__ = mocker.Mock(return_value=io.BytesIO(response_body))
    mock_response.__exit__ = mocker.Mock(return_value=False)
    mocker.patch.object(lonis.mtg.cache._opener, "open", return_value=mock_response)
    cache = MtgDataCache(cache_dir=tmp_path)
    with pytest.raises(RuntimeError, match="Cache still corrupt after re-download"):
        cache.load()
