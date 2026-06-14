"""MtgDataCache — downloads and caches the AtomicCards dataset from mtgjson.com."""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path
from typing import Any
from typing import cast

logger = logging.getLogger(__name__)

_ATOMIC_CARDS_URL = "https://mtgjson.com/api/v5/AtomicCards.json"
_DEFAULT_CACHE_DIR = Path.home() / ".cache" / "lonis"


class MtgDataCache:
    """
    Manages a local cache of the AtomicCards JSON file from mtgjson.com.

    Downloads automatically when missing or older than today's date.
    """

    def __init__(self, cache_dir: Path = _DEFAULT_CACHE_DIR) -> None:
        """
        Create an MtgDataCache.

        Args:
            cache_dir: Directory to store the cached file. Defaults to ~/.cache/lonis.
        """
        self._cache_dir = cache_dir
        self._cache_file = cache_dir / "AtomicCards.json"

    def load(self) -> dict[str, list[dict[str, Any]]]:
        """
        Return the AtomicCards data, downloading it if missing or stale.

        Returns:
            Dict mapping card name to list of face objects.

        Raises:
            RuntimeError: If the download fails.
        """
        if self._is_stale():
            self._download()
        return self._read()

    def _is_stale(self) -> bool:
        if not self._cache_file.exists():
            return True
        mtime = date.fromtimestamp(self._cache_file.stat().st_mtime)
        # Stale means a prior calendar day (local time), not strictly 24 hours old.
        return mtime < date.today()

    def _download(self) -> None:
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Downloading AtomicCards from %s", _ATOMIC_CARDS_URL)
        try:
            urllib.request.urlretrieve(_ATOMIC_CARDS_URL, self._cache_file)
        except (urllib.error.URLError, OSError) as exc:
            raise RuntimeError(f"Failed to download {_ATOMIC_CARDS_URL}: {exc}") from exc
        logger.info("AtomicCards cached at %s", self._cache_file)

    def _read(self) -> dict[str, list[dict[str, Any]]]:
        try:
            return self._parse()
        except (json.JSONDecodeError, KeyError, OSError):
            logger.warning("Cache file corrupt or invalid, re-downloading")
            self._cache_file.unlink(missing_ok=True)
            self._download()
        try:
            return self._parse()
        except (json.JSONDecodeError, KeyError, OSError) as exc:
            raise RuntimeError(f"Cache still corrupt after re-download: {exc}") from exc

    def _parse(self) -> dict[str, list[dict[str, Any]]]:
        """Open and parse the cache file, returning the card data dict."""
        with self._cache_file.open() as fh:
            raw: dict[str, Any] = json.load(fh)
        return cast(dict[str, list[dict[str, Any]]], raw["data"])
