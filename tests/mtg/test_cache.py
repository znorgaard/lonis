"""Tests for MtgDataCache."""

import json
import os
import time
from pathlib import Path
from typing import Any

import pytest
from pytest_mock import MockerFixture

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
    mock_retrieve = mocker.patch("urllib.request.urlretrieve")
    cache = MtgDataCache(cache_dir=tmp_path)
    result = cache.load()
    mock_retrieve.assert_not_called()
    assert "Elvish Mystic" in result


def test_load_redownloads_when_stale(tmp_path: Path, mocker: MockerFixture) -> None:
    cache_file = tmp_path / "AtomicCards.json"
    _write_cache(cache_file, _SAMPLE_DATA)
    _set_mtime_yesterday(cache_file)

    def fake_download(_url: str, dest: str) -> None:
        Path(dest).write_text(json.dumps(_UPDATED_DATA))

    mocker.patch("urllib.request.urlretrieve", side_effect=fake_download)
    cache = MtgDataCache(cache_dir=tmp_path)
    result = cache.load()
    assert "Goblin Guide" in result
    assert "Elvish Mystic" not in result


def test_load_downloads_when_missing(tmp_path: Path, mocker: MockerFixture) -> None:
    def fake_download(_url: str, dest: str) -> None:
        Path(dest).write_text(json.dumps(_SAMPLE_DATA))

    mock_retrieve = mocker.patch("urllib.request.urlretrieve", side_effect=fake_download)
    cache = MtgDataCache(cache_dir=tmp_path)
    result = cache.load()
    mock_retrieve.assert_called_once()
    assert "Elvish Mystic" in result


def test_load_redownloads_corrupt_cache(tmp_path: Path, mocker: MockerFixture) -> None:
    cache_file = tmp_path / "AtomicCards.json"
    cache_file.write_text("this is not valid json {{{")

    def fake_download(_url: str, dest: str) -> None:
        Path(dest).write_text(json.dumps(_SAMPLE_DATA))

    mock_retrieve = mocker.patch("urllib.request.urlretrieve", side_effect=fake_download)
    cache = MtgDataCache(cache_dir=tmp_path)
    result = cache.load()
    mock_retrieve.assert_called_once()
    assert "Elvish Mystic" in result


def test_load_raises_on_download_failure(tmp_path: Path, mocker: MockerFixture) -> None:
    mocker.patch("urllib.request.urlretrieve", side_effect=OSError("connection refused"))
    cache = MtgDataCache(cache_dir=tmp_path)
    with pytest.raises(RuntimeError, match="Failed to download"):
        cache.load()
