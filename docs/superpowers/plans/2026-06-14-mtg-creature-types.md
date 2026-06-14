# MTG Creature Types Tool Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `creature-types` CLI tool that reports every Magic: The Gathering creature type and the number of unique cards with that type, filtered by format legality, with results written to a TSV file.

**Architecture:** A `lonis/mtg/` sub-package owns all MTG domain logic — `MtgDataCache` handles downloading and caching AtomicCards JSON from mtgjson.com with daily invalidation, `MtgCard` wraps a single unique card, and `MtgCardSet` provides filter and aggregation methods. The `creature_types` CLI tool in `lonis/tools/` is a thin wrapper that chains these together and writes output via fgmetric.

**Tech Stack:** Python 3.12+, fgmetric (TSV output), urllib.request (download), pytest + pytest-mock (tests), defopt (CLI dispatch), ruff + mypy (lint/types)

---

## File Map

| File | Action | Purpose |
|---|---|---|
| `lonis/mtg/__init__.py` | Create | Package marker |
| `lonis/mtg/card.py` | Create | `MtgCard` frozen dataclass |
| `lonis/mtg/card_set.py` | Create | `MtgCardSet` collection with filters |
| `lonis/mtg/cache.py` | Create | `MtgDataCache` — download + daily cache |
| `lonis/tools/creature_types.py` | Create | `CreatureTypeMetric` + `creature_types()` CLI |
| `lonis/main.py` | Modify | Register `creature_types` in `_tools` |
| `pyproject.toml` | Modify | Add `fgmetric` runtime dependency |
| `tests/mtg/__init__.py` | Create | Package marker |
| `tests/mtg/test_card.py` | Create | Unit tests for `MtgCard` |
| `tests/mtg/test_card_set.py` | Create | Unit tests for `MtgCardSet` |
| `tests/mtg/test_cache.py` | Create | Unit tests for `MtgDataCache` |
| `tests/tools/test_creature_types.py` | Create | End-to-end test for `creature_types` tool |

---

## Review Protocol

After each marked review phase:
1. Run `/code-review` and `/review-as-znorgaard` **in parallel** (two independent subagents).
2. Aggregate their feedback into a single list.
3. Incorporate all reasonable feedback; skip anything that doesn't apply to this codebase.
4. Re-run `uv run --locked poe check-all` after changes.
5. Re-run both reviews. Repeat until feedback is only minor nits or inapplicable suggestions.
6. Commit any incorporated changes.

---

## Task 1: Add fgmetric dependency

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Add fgmetric via uv**

```bash
uv add fgmetric
```

Expected: `pyproject.toml` gains `"fgmetric"` in `[project] dependencies`, and `uv.lock` is updated.

- [ ] **Step 2: Verify the import works**

```bash
uv run python -c "from fgmetric import Metric, MetricWriter; print('ok')"
```

Expected output: `ok`

- [ ] **Step 3: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "feat: add fgmetric dependency"
```

---

## Task 2: `MtgCard` dataclass

**Files:**
- Create: `lonis/mtg/__init__.py`
- Create: `lonis/mtg/card.py`
- Create: `tests/mtg/__init__.py`
- Create: `tests/mtg/test_card.py`

- [ ] **Step 1: Create package markers**

`lonis/mtg/__init__.py`:
```python
"""MTG data models and utilities for the lonis toolkit."""
```

`tests/mtg/__init__.py`:
```python
```

- [ ] **Step 2: Write the failing tests**

`tests/mtg/test_card.py`:
```python
"""Tests for MtgCard."""

from lonis.mtg.card import MtgCard


def _face(
    *,
    layout: str = "normal",
    types: list[str] | None = None,
    subtypes: list[str] | None = None,
    supertypes: list[str] | None = None,
    legalities: dict[str, str] | None = None,
    is_funny: bool = False,
) -> dict:
    return {
        "layout": layout,
        "types": types or [],
        "subtypes": subtypes or [],
        "supertypes": supertypes or [],
        "legalities": legalities or {},
        "isFunny": is_funny,
    }


def test_from_atomic_entry_single_face():
    faces = [_face(types=["Creature"], subtypes=["Human", "Warrior"], supertypes=["Legendary"],
                   legalities={"commander": "Legal", "modern": "Legal"})]
    card = MtgCard.from_atomic_entry("Adanto Vanguard", faces)
    assert card is not None
    assert card.name == "Adanto Vanguard"
    assert card.layout == "normal"
    assert card.types == frozenset({"Creature"})
    assert card.subtypes == frozenset({"Human", "Warrior"})
    assert card.supertypes == frozenset({"Legendary"})
    assert card.legalities == {"commander": "Legal", "modern": "Legal"}
    assert card.is_funny is False


def test_from_atomic_entry_multi_face_aggregates_types():
    faces = [
        _face(layout="transform", types=["Creature"], subtypes=["Human", "Warrior"],
              supertypes=[], legalities={"commander": "Legal"}),
        _face(layout="transform", types=["Creature"], subtypes=["Werewolf"],
              supertypes=[], legalities={"commander": "Legal"}),
    ]
    card = MtgCard.from_atomic_entry("Huntmaster of the Fells // Ravager of the Fells", faces)
    assert card is not None
    assert card.subtypes == frozenset({"Human", "Warrior", "Werewolf"})
    assert card.types == frozenset({"Creature"})
    assert card.layout == "transform"


def test_from_atomic_entry_token_returns_none():
    faces = [_face(layout="token", types=["Creature"], subtypes=["Soldier"],
                   legalities={"commander": "Not Legal"})]
    assert MtgCard.from_atomic_entry("Soldier Token", faces) is None


def test_from_atomic_entry_is_funny_flag():
    faces = [_face(types=["Creature"], subtypes=["Chicken"], is_funny=True,
                   legalities={"commander": "Not Legal"})]
    card = MtgCard.from_atomic_entry("Chicken (Unhinged)", faces)
    assert card is not None
    assert card.is_funny is True
```

- [ ] **Step 3: Run the tests to verify they fail**

```bash
uv run --locked pytest tests/mtg/test_card.py -v
```

Expected: `ImportError` or `ModuleNotFoundError` — `lonis.mtg.card` does not exist yet.

- [ ] **Step 4: Implement `MtgCard`**

`lonis/mtg/card.py`:
```python
"""MtgCard dataclass representing a single unique Magic: The Gathering card."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class MtgCard:
    """A single unique Magic: The Gathering card, aggregated across all of its faces."""

    name: str
    layout: str
    types: frozenset[str]
    subtypes: frozenset[str]
    supertypes: frozenset[str]
    legalities: dict[str, str]
    is_funny: bool

    @classmethod
    def from_atomic_entry(cls, name: str, faces: list[dict[str, Any]]) -> MtgCard | None:
        """Build an MtgCard from an AtomicCards entry.

        Args:
            name: The card name (the key in the AtomicCards dict).
            faces: List of face objects for this card name. Single-face cards have one element.

        Returns:
            An MtgCard, or None if the card is a token.
        """
        first = faces[0]
        layout: str = first.get("layout", "")
        if layout == "token":
            return None
        types: frozenset[str] = frozenset()
        subtypes: frozenset[str] = frozenset()
        supertypes: frozenset[str] = frozenset()
        for face in faces:
            types = types | frozenset(face.get("types", []))
            subtypes = subtypes | frozenset(face.get("subtypes", []))
            supertypes = supertypes | frozenset(face.get("supertypes", []))
        return cls(
            name=name,
            layout=layout,
            types=types,
            subtypes=subtypes,
            supertypes=supertypes,
            legalities=dict(first.get("legalities", {})),
            is_funny=bool(first.get("isFunny", False)),
        )
```

- [ ] **Step 5: Run the tests to verify they pass**

```bash
uv run --locked pytest tests/mtg/test_card.py -v
```

Expected: 4 tests pass.

- [ ] **Step 6: Commit**

```bash
git add lonis/mtg/__init__.py lonis/mtg/card.py tests/mtg/__init__.py tests/mtg/test_card.py
git commit -m "feat: add MtgCard dataclass"
```

---

## Task 3: `MtgCardSet` collection

**Files:**
- Create: `lonis/mtg/card_set.py`
- Create: `tests/mtg/test_card_set.py`

- [ ] **Step 1: Write the failing tests**

`tests/mtg/test_card_set.py`:
```python
"""Tests for MtgCardSet."""

import pytest

from lonis.mtg.card import MtgCard
from lonis.mtg.card_set import MtgCardSet


def _make_card(
    name: str,
    *,
    types: list[str] | None = None,
    subtypes: list[str] | None = None,
    legalities: dict[str, str] | None = None,
) -> MtgCard:
    return MtgCard(
        name=name,
        layout="normal",
        types=frozenset(types or []),
        subtypes=frozenset(subtypes or []),
        supertypes=frozenset(),
        legalities=legalities or {},
        is_funny=False,
    )


def test_from_atomic_data_excludes_tokens():
    data: dict = {
        "Elvish Mystic": [{"layout": "normal", "types": ["Creature"], "subtypes": ["Elf", "Druid"],
                            "supertypes": [], "legalities": {"commander": "Legal"}, "isFunny": False}],
        "Soldier Token": [{"layout": "token", "types": ["Creature"], "subtypes": ["Soldier"],
                           "supertypes": [], "legalities": {}, "isFunny": False}],
    }
    card_set = MtgCardSet.from_atomic_data(data)
    names = {c.name for c in card_set}
    assert "Elvish Mystic" in names
    assert "Soldier Token" not in names


def test_filter_format_keeps_legal_cards():
    cards = (
        _make_card("Legal Card", legalities={"commander": "Legal"}),
        _make_card("Banned Card", legalities={"commander": "Banned"}),
        _make_card("Not Legal Card", legalities={"commander": "Not Legal"}),
    )
    result = MtgCardSet(cards).filter_format("commander")
    assert {c.name for c in result} == {"Legal Card"}


def test_filter_format_raises_on_unknown_format():
    cards = (_make_card("Card", legalities={"commander": "Legal", "modern": "Legal"}),)
    with pytest.raises(ValueError, match="unknown_format"):
        MtgCardSet(cards).filter_format("unknown_format")


def test_filter_format_empty_card_set_does_not_raise():
    result = MtgCardSet(()).filter_format("commander")
    assert list(result) == []


def test_filter_creatures_keeps_only_creature_cards():
    cards = (
        _make_card("Creature Card", types=["Creature"]),
        _make_card("Instant Card", types=["Instant"]),
        _make_card("Artifact Creature", types=["Artifact", "Creature"]),
        _make_card("Tribal Instant", types=["Tribal", "Instant"]),
    )
    result = MtgCardSet(cards).filter_creatures()
    assert {c.name for c in result} == {"Creature Card", "Artifact Creature"}


def test_creature_type_counts():
    cards = (
        _make_card("Elvish Mystic", types=["Creature"], subtypes=["Elf", "Druid"]),
        _make_card("Llanowar Elves", types=["Creature"], subtypes=["Elf", "Druid"]),
        _make_card("Goblin Guide", types=["Creature"], subtypes=["Goblin", "Scout"]),
    )
    counts = MtgCardSet(cards).creature_type_counts()
    assert counts == {"Elf": 2, "Druid": 2, "Goblin": 1, "Scout": 1}
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
uv run --locked pytest tests/mtg/test_card_set.py -v
```

Expected: `ImportError` — `lonis.mtg.card_set` does not exist yet.

- [ ] **Step 3: Implement `MtgCardSet`**

`lonis/mtg/card_set.py`:
```python
"""MtgCardSet — an immutable collection of MtgCard with filter and aggregation methods."""

from __future__ import annotations

from collections import Counter
from typing import Any
from typing import Iterator

from lonis.mtg.card import MtgCard


class MtgCardSet:
    """An immutable collection of unique Magic: The Gathering cards."""

    def __init__(self, cards: tuple[MtgCard, ...]) -> None:
        """Create an MtgCardSet from a tuple of cards.

        Args:
            cards: The cards in this set.
        """
        self._cards = cards

    def __iter__(self) -> Iterator[MtgCard]:
        """Iterate over the cards in this set."""
        return iter(self._cards)

    @classmethod
    def from_atomic_data(cls, data: dict[str, list[dict[str, Any]]]) -> MtgCardSet:
        """Build an MtgCardSet from a parsed AtomicCards dict.

        Args:
            data: The value of the "data" key in AtomicCards JSON — card name to list of faces.

        Returns:
            An MtgCardSet containing all non-token cards.
        """
        cards = []
        for name, faces in data.items():
            card = MtgCard.from_atomic_entry(name, faces)
            if card is not None:
                cards.append(card)
        return cls(tuple(cards))

    def filter_format(self, fmt: str) -> MtgCardSet:
        """Return a new MtgCardSet containing only cards legal in the given format.

        Args:
            fmt: Format name, e.g. "commander", "modern", "standard".

        Returns:
            A filtered MtgCardSet.

        Raises:
            ValueError: If fmt is not a recognized format name.
        """
        if self._cards:
            valid_formats = set(self._cards[0].legalities.keys())
            if fmt not in valid_formats:
                raise ValueError(
                    f"Unknown format {fmt!r}. Valid formats: {sorted(valid_formats)}"
                )
        return MtgCardSet(
            tuple(c for c in self._cards if c.legalities.get(fmt) == "Legal")
        )

    def filter_creatures(self) -> MtgCardSet:
        """Return a new MtgCardSet containing only cards with the Creature type.

        Returns:
            A filtered MtgCardSet.
        """
        return MtgCardSet(tuple(c for c in self._cards if "Creature" in c.types))

    def creature_type_counts(self) -> dict[str, int]:
        """Count how many cards have each creature subtype.

        Returns:
            A dict mapping creature subtype to number of cards with that subtype.
        """
        counter: Counter[str] = Counter()
        for card in self._cards:
            for subtype in card.subtypes:
                counter[subtype] += 1
        return dict(counter)
```

- [ ] **Step 4: Run the tests to verify they pass**

```bash
uv run --locked pytest tests/mtg/test_card_set.py -v
```

Expected: 6 tests pass.

- [ ] **Step 5: Commit**

```bash
git add lonis/mtg/card_set.py tests/mtg/test_card_set.py
git commit -m "feat: add MtgCardSet collection with filter and aggregation"
```

---

## Review Phase 1 (after Tasks 1–3)

Run both reviews in parallel, then iterate until feedback is minor.

- [ ] **Step 1: Run parallel reviews**

Dispatch simultaneously:
- `/code-review` on the current branch diff
- `/review-as-znorgaard` on the current branch diff

- [ ] **Step 2: Aggregate and triage feedback**

Collect all feedback. For each item decide: incorporate, skip (with reason), or defer.

- [ ] **Step 3: Incorporate reasonable feedback**

Make changes, then re-run:
```bash
uv run --locked poe check-all
```

Expected: all checks pass.

- [ ] **Step 4: Re-run both reviews**

Repeat Steps 1–3 until both reviews return only minor nits or inapplicable suggestions.

- [ ] **Step 5: Commit any incorporated changes**

```bash
git add -p
git commit -m "refactor: incorporate review feedback on data models"
```

---

## Task 4: `MtgDataCache`

**Files:**
- Create: `lonis/mtg/cache.py`
- Create: `tests/mtg/test_cache.py`

- [ ] **Step 1: Write the failing tests**

`tests/mtg/test_cache.py`:
```python
"""Tests for MtgDataCache."""

import json
import os
import time
from pathlib import Path

from pytest_mock import MockerFixture

from lonis.mtg.cache import MtgDataCache


_SAMPLE_DATA = {
    "data": {
        "Elvish Mystic": [{"layout": "normal", "types": ["Creature"], "subtypes": ["Elf", "Druid"],
                           "supertypes": [], "legalities": {"commander": "Legal"}, "isFunny": False}],
    }
}

_UPDATED_DATA = {
    "data": {
        "Goblin Guide": [{"layout": "normal", "types": ["Creature"], "subtypes": ["Goblin", "Scout"],
                          "supertypes": [], "legalities": {"commander": "Legal"}, "isFunny": False}],
    }
}


def _write_cache(cache_file: Path, data: dict) -> None:
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

    def fake_download(url: str, dest: str) -> None:
        Path(dest).write_text(json.dumps(_UPDATED_DATA))

    mocker.patch("urllib.request.urlretrieve", side_effect=fake_download)
    cache = MtgDataCache(cache_dir=tmp_path)
    result = cache.load()
    assert "Goblin Guide" in result
    assert "Elvish Mystic" not in result


def test_load_downloads_when_missing(tmp_path: Path, mocker: MockerFixture) -> None:
    def fake_download(url: str, dest: str) -> None:
        Path(dest).write_text(json.dumps(_SAMPLE_DATA))

    mock_retrieve = mocker.patch("urllib.request.urlretrieve", side_effect=fake_download)
    cache = MtgDataCache(cache_dir=tmp_path)
    result = cache.load()
    mock_retrieve.assert_called_once()
    assert "Elvish Mystic" in result


def test_load_redownloads_corrupt_cache(tmp_path: Path, mocker: MockerFixture) -> None:
    cache_file = tmp_path / "AtomicCards.json"
    cache_file.write_text("this is not valid json {{{")

    def fake_download(url: str, dest: str) -> None:
        Path(dest).write_text(json.dumps(_SAMPLE_DATA))

    mock_retrieve = mocker.patch("urllib.request.urlretrieve", side_effect=fake_download)
    cache = MtgDataCache(cache_dir=tmp_path)
    result = cache.load()
    mock_retrieve.assert_called_once()
    assert "Elvish Mystic" in result


def test_load_raises_on_download_failure(tmp_path: Path, mocker: MockerFixture) -> None:
    import pytest
    mocker.patch("urllib.request.urlretrieve", side_effect=OSError("connection refused"))
    cache = MtgDataCache(cache_dir=tmp_path)
    with pytest.raises(RuntimeError, match="Failed to download"):
        cache.load()
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
uv run --locked pytest tests/mtg/test_cache.py -v
```

Expected: `ImportError` — `lonis.mtg.cache` does not exist yet.

- [ ] **Step 3: Implement `MtgDataCache`**

`lonis/mtg/cache.py`:
```python
"""MtgDataCache — downloads and caches the AtomicCards dataset from mtgjson.com."""

from __future__ import annotations

import json
import logging
import urllib.request
from datetime import date
from pathlib import Path
from typing import Any
from typing import cast

logger = logging.getLogger(__name__)

_ATOMIC_CARDS_URL = "https://mtgjson.com/api/v5/AtomicCards.json"
_DEFAULT_CACHE_DIR = Path.home() / ".cache" / "lonis"


class MtgDataCache:
    """Manages a local cache of the AtomicCards JSON file from mtgjson.com.

    Downloads automatically when missing or older than today's date.
    """

    def __init__(self, cache_dir: Path = _DEFAULT_CACHE_DIR) -> None:
        """Create an MtgDataCache.

        Args:
            cache_dir: Directory to store the cached file. Defaults to ~/.cache/lonis.
        """
        self._cache_dir = cache_dir
        self._cache_file = cache_dir / "AtomicCards.json"

    def load(self) -> dict[str, list[dict[str, Any]]]:
        """Return the AtomicCards data, downloading it if missing or stale.

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
        return mtime < date.today()

    def _download(self) -> None:
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Downloading AtomicCards from %s", _ATOMIC_CARDS_URL)
        try:
            urllib.request.urlretrieve(_ATOMIC_CARDS_URL, self._cache_file)
        except Exception as exc:
            raise RuntimeError(
                f"Failed to download {_ATOMIC_CARDS_URL}: {exc}"
            ) from exc
        logger.info("AtomicCards cached at %s", self._cache_file)

    def _read(self) -> dict[str, list[dict[str, Any]]]:
        try:
            with self._cache_file.open() as fh:
                raw: dict[str, Any] = json.load(fh)
            return cast(dict[str, list[dict[str, Any]]], raw["data"])
        except (json.JSONDecodeError, KeyError, OSError):
            logger.warning("Cache file corrupt or invalid, re-downloading")
            self._cache_file.unlink(missing_ok=True)
            self._download()
            with self._cache_file.open() as fh:
                raw = json.load(fh)
            return cast(dict[str, list[dict[str, Any]]], raw["data"])
```

- [ ] **Step 4: Run the tests to verify they pass**

```bash
uv run --locked pytest tests/mtg/test_cache.py -v
```

Expected: 5 tests pass.

- [ ] **Step 5: Commit**

```bash
git add lonis/mtg/cache.py tests/mtg/test_cache.py
git commit -m "feat: add MtgDataCache with daily cache invalidation"
```

---

## Task 5: `creature_types` tool

**Files:**
- Create: `lonis/tools/creature_types.py`
- Create: `tests/tools/test_creature_types.py`

- [ ] **Step 1: Write the failing tests**

`tests/tools/test_creature_types.py`:
```python
"""End-to-end tests for the creature_types tool."""

from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from lonis.mtg.cache import MtgDataCache
from lonis.tools.creature_types import CreatureTypeMetric
from lonis.tools.creature_types import creature_types


_ATOMIC_DATA = {
    "Elvish Mystic": [{"layout": "normal", "types": ["Creature"], "subtypes": ["Elf", "Druid"],
                       "supertypes": [], "legalities": {"commander": "Legal", "modern": "Legal"},
                       "isFunny": False}],
    "Goblin Guide": [{"layout": "normal", "types": ["Creature"], "subtypes": ["Goblin", "Scout"],
                      "supertypes": [], "legalities": {"commander": "Legal", "modern": "Legal"},
                      "isFunny": False}],
    "Lightning Bolt": [{"layout": "normal", "types": ["Instant"], "subtypes": [],
                        "supertypes": [], "legalities": {"commander": "Legal", "modern": "Legal"},
                        "isFunny": False}],
    "Ancestral Recall": [{"layout": "normal", "types": ["Instant"], "subtypes": [],
                          "supertypes": [],
                          "legalities": {"commander": "Banned", "modern": "Not Legal"},
                          "isFunny": False}],
    "Goblin Token": [{"layout": "token", "types": ["Creature"], "subtypes": ["Goblin"],
                      "supertypes": [], "legalities": {}, "isFunny": False}],
}


def test_creature_types_writes_correct_types(tmp_path: Path, mocker: MockerFixture) -> None:
    mocker.patch.object(MtgDataCache, "load", return_value=_ATOMIC_DATA)
    output = tmp_path / "out.tsv"
    creature_types(output)
    creature_type_names = {m.creature_type for m in CreatureTypeMetric.read(output)}
    assert creature_type_names == {"Elf", "Druid", "Goblin", "Scout"}


def test_creature_types_counts_are_correct(tmp_path: Path, mocker: MockerFixture) -> None:
    mocker.patch.object(MtgDataCache, "load", return_value=_ATOMIC_DATA)
    output = tmp_path / "out.tsv"
    creature_types(output)
    metrics = {m.creature_type: m.count for m in CreatureTypeMetric.read(output)}
    assert metrics["Elf"] == 1
    assert metrics["Druid"] == 1
    assert metrics["Goblin"] == 1
    assert metrics["Scout"] == 1


def test_creature_types_sorted_count_desc_then_alpha(tmp_path: Path, mocker: MockerFixture) -> None:
    data = {
        "Elvish Mystic": [{"layout": "normal", "types": ["Creature"],
                           "subtypes": ["Elf", "Druid"], "supertypes": [],
                           "legalities": {"commander": "Legal"}, "isFunny": False}],
        "Llanowar Elves": [{"layout": "normal", "types": ["Creature"],
                            "subtypes": ["Elf", "Druid"], "supertypes": [],
                            "legalities": {"commander": "Legal"}, "isFunny": False}],
        "Goblin Guide": [{"layout": "normal", "types": ["Creature"],
                          "subtypes": ["Goblin", "Scout"], "supertypes": [],
                          "legalities": {"commander": "Legal"}, "isFunny": False}],
    }
    mocker.patch.object(MtgDataCache, "load", return_value=data)
    output = tmp_path / "sorted.tsv"
    creature_types(output)
    metrics = list(CreatureTypeMetric.read(output))
    # Druid=2, Elf=2 (tie → alpha: Druid < Elf), Goblin=1, Scout=1 (tie → Goblin < Scout)
    assert metrics[0].creature_type == "Druid"
    assert metrics[1].creature_type == "Elf"
    assert metrics[2].creature_type == "Goblin"
    assert metrics[3].creature_type == "Scout"


def test_creature_types_invalid_format_raises(tmp_path: Path, mocker: MockerFixture) -> None:
    mocker.patch.object(MtgDataCache, "load", return_value=_ATOMIC_DATA)
    output = tmp_path / "out.tsv"
    with pytest.raises(ValueError, match="notaformat"):
        creature_types(output, fmt="notaformat")


def test_creature_types_empty_result_writes_header_only(
    tmp_path: Path, mocker: MockerFixture
) -> None:
    data = {
        "Lightning Bolt": [{"layout": "normal", "types": ["Instant"], "subtypes": [],
                            "supertypes": [], "legalities": {"commander": "Legal"}, "isFunny": False}],
    }
    mocker.patch.object(MtgDataCache, "load", return_value=data)
    output = tmp_path / "empty.tsv"
    creature_types(output)
    metrics = list(CreatureTypeMetric.read(output))
    assert metrics == []
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
uv run --locked pytest tests/tools/test_creature_types.py -v
```

Expected: `ImportError` — `lonis.tools.creature_types` does not exist yet.

- [ ] **Step 3: Implement the tool**

`lonis/tools/creature_types.py`:
```python
"""CLI tool: report creature types and their card counts for a given Magic format."""

from __future__ import annotations

import logging
from pathlib import Path

from fgmetric import Metric
from fgmetric import MetricWriter

from lonis.mtg.cache import MtgDataCache
from lonis.mtg.card_set import MtgCardSet

logger = logging.getLogger(__name__)


class CreatureTypeMetric(Metric):
    """One row of creature type output: the type name and number of cards with that type."""

    creature_type: str
    count: int


def creature_types(output: Path, *, fmt: str = "commander") -> None:
    """Report all creature types and the number of cards with each type in a format.

    Args:
        output: Path to write the output TSV file.
        fmt: Magic: The Gathering format to filter cards by (e.g. commander, modern, standard).
    """
    data = MtgDataCache().load()
    card_set = MtgCardSet.from_atomic_data(data)
    counts = card_set.filter_format(fmt).filter_creatures().creature_type_counts()
    if not counts:
        logger.warning("No creature types found for format %r — writing empty output", fmt)
    metrics = [
        CreatureTypeMetric(creature_type=ct, count=count)
        for ct, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    ]
    with MetricWriter.open(CreatureTypeMetric, output) as writer:
        writer.writeall(metrics)
```

- [ ] **Step 4: Run the tests to verify they pass**

```bash
uv run --locked pytest tests/tools/test_creature_types.py -v
```

Expected: 5 tests pass.

- [ ] **Step 5: Commit**

```bash
git add lonis/tools/creature_types.py tests/tools/test_creature_types.py
git commit -m "feat: add creature_types CLI tool"
```

---

## Review Phase 2 (after Tasks 4–5)

Run both reviews in parallel, then iterate until feedback is minor.

- [ ] **Step 1: Run parallel reviews**

Dispatch simultaneously:
- `/code-review` on the current branch diff
- `/review-as-znorgaard` on the current branch diff

- [ ] **Step 2: Aggregate and triage feedback**

Collect all feedback. For each item decide: incorporate, skip (with reason), or defer.

- [ ] **Step 3: Incorporate reasonable feedback**

Make changes, then re-run:
```bash
uv run --locked poe check-all
```

Expected: all checks pass.

- [ ] **Step 4: Re-run both reviews**

Repeat Steps 1–3 until both reviews return only minor nits or inapplicable suggestions.

- [ ] **Step 5: Commit any incorporated changes**

```bash
git add -p
git commit -m "refactor: incorporate review feedback on cache and tool"
```

---

## Task 6: Register tool and verify

**Files:**
- Modify: `lonis/main.py`

- [ ] **Step 1: Register `creature_types` in `main.py`**

Replace the full contents of `lonis/main.py` with:

```python
"""CLI entry point for the lonis toolkit."""

import logging
import sys
from collections.abc import Callable

import defopt

from lonis.tools.creature_types import creature_types
from lonis.tools.hello import hello

logger = logging.getLogger(__name__)

_tools: list[Callable[..., None]] = [
    hello,
    creature_types,
]


def setup_logging(level: str = "INFO") -> None:
    """Set up basic logging to print to the console.

    Args:
        level: Logging level string (e.g. "INFO", "DEBUG", "WARNING").
    """
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(name)s:%(funcName)s:%(lineno)s [%(levelname)s]: %(message)s",
    )


def run() -> None:
    """Set up logging, then hand over to defopt for running command line tools."""
    setup_logging()
    logger.info("Executing: " + " ".join(sys.argv))
    defopt.run(
        funcs=_tools,
        argv=sys.argv[1:],
    )
    logger.info("Finished executing successfully.")
```

- [ ] **Step 2: Run the full check suite**

```bash
uv run --locked poe check-all
```

Expected: format check, lint, type check, and all tests pass. Fix any issues before proceeding.

- [ ] **Step 3: Smoke test the CLI**

```bash
uv run lonis creature-types /tmp/creature_types.tsv && head /tmp/creature_types.tsv
```

Expected: downloads AtomicCards (first run only), then writes a TSV with `creature_type` and `count` columns populated with real data.

- [ ] **Step 4: Commit**

```bash
git add lonis/main.py
git commit -m "feat: register creature_types tool in CLI"
```
