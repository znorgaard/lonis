# MTG Creature Types Tool — Design Spec

**Date:** 2026-06-14  
**Status:** Approved

## Overview

Add a `creature-types` CLI tool to `lonis` that reports every creature type in Magic: The Gathering and how many unique cards have each type, filtered by format legality. Output is a TSV file written via fgmetric.

Data comes from [mtgjson.com](https://mtgjson.com) (AtomicCards), cached locally with daily invalidation.

---

## Source Data

**File:** [AtomicCards](https://mtgjson.com/downloads/all-files/) — one entry per unique card name; naturally deduplicates reprints.

**Key card fields used:**
- `name` — card name (the dict key in AtomicCards)
- `types` — e.g. `["Creature"]`
- `subtypes` — creature types, e.g. `["Human", "Wizard"]`
- `supertypes` — e.g. `["Legendary"]`
- `legalities` — map of format name → `"Legal"` | `"Banned"` | `"Restricted"` | `"Not Legal"`
- `layout` — used to exclude tokens (`layout == "token"`)
- `isFunny` — present but not used directly; format legality filter handles exclusion

**Multi-face cards** (transform, meld, split) are stored as a list of face objects under a single name key. Types and subtypes are aggregated across all faces.

**Exclusions:**
- Tokens (`layout == "token"`)
- Cards not legal in the selected format
- Cards where `"Creature"` is not in `types` (tribal cards do not count)

---

## Architecture

```
lonis/
  mtg/
    __init__.py
    cache.py        # download + daily cache invalidation
    card.py         # MtgCard dataclass
    card_set.py     # MtgCardSet collection with filter/aggregate methods
  tools/
    creature_types.py   # CreatureTypeMetric + CLI entry point
  main.py               # register creature_types in _tools

tests/
  mtg/
    __init__.py
    test_cache.py
    test_card.py
    test_card_set.py
  tools/
    test_creature_types.py
```

Data flows in one direction: `cache → card → card_set → tool → fgmetric TSV`.

---

## Data Layer (`lonis/mtg/`)

### `cache.py` — `MtgDataCache`

- Cache location: `~/.cache/lonis/AtomicCards.json`
- On access: compare the file's modification date to today's date. If stale (or missing), re-download from mtgjson.com.
- If the cached file is corrupt (JSON parse error), delete it and re-download.
- Returns `dict[str, list[dict[str, Any]]]` — card name → list of face objects.
- Download failures (network error, non-200 response) raise with the URL and HTTP status.

### `card.py` — `MtgCard`

A frozen dataclass constructed from one AtomicCards entry (all faces for a given name).

```python
@dataclass(frozen=True)
class MtgCard:
    name: str
    layout: str
    types: frozenset[str]
    subtypes: frozenset[str]
    supertypes: frozenset[str]
    legalities: dict[str, str]
    is_funny: bool
```

**`MtgCard.from_atomic_entry(name: str, faces: list[dict[str, Any]]) -> MtgCard`**

- Aggregates `types`, `subtypes`, `supertypes` across all faces via union.
- Uses `layout` and `legalities` from the first face (consistent across faces).
- Returns `None` for tokens (`layout == "token"`) so the caller can skip them.

### `card_set.py` — `MtgCardSet`

Wraps `tuple[MtgCard, ...]`. Constructed via `MtgCardSet.from_cache(cache: MtgDataCache)`.

| Method | Returns | Description |
|---|---|---|
| `filter_format(fmt: str)` | `MtgCardSet` | Keeps cards where `legalities[fmt] == "Legal"`. Raises `ValueError` with valid format names if `fmt` is unrecognized. |
| `filter_creatures()` | `MtgCardSet` | Keeps cards where `"Creature" in types`. |
| `creature_type_counts()` | `dict[str, int]` | Counts distinct cards per subtype. |

Valid format names are derived from the legalities keys on the loaded cards.

---

## Tool Layer (`lonis/tools/creature_types.py`)

### `CreatureTypeMetric`

```python
class CreatureTypeMetric(Metric):
    creature_type: str
    count: int
```

### CLI function

```python
def creature_types(output: Path, *, fmt: str = "commander") -> None:
```

Registered in `main.py`'s `_tools` list. Steps:

1. Load `MtgDataCache` (auto-downloads if missing/stale).
2. Build `MtgCardSet.from_cache(cache)`.
3. Call `.filter_format(fmt).filter_creatures().creature_type_counts()`.
4. Sort results: count descending, then creature type alphabetically for ties.
5. Write `CreatureTypeMetric` rows via `MetricWriter`.

---

## Error Handling

| Condition | Behavior |
|---|---|
| Unrecognized `--fmt` value | `ValueError` listing all valid format names |
| Download failure | Raise with URL and HTTP status code |
| Corrupt cache file | Delete and re-download |
| Empty result set | Write header-only TSV, log warning |

Prefer loud failures over silent wrong answers throughout.

---

## Testing

All test inputs built in-code (dicts, dataclass instances) — no fixture files.

- **`test_cache.py`** — mock network calls; verify: stale file triggers re-download, same-day cache hit skips download, corrupt file is deleted and re-downloaded.
- **`test_card.py`** — `MtgCard.from_atomic_entry`: single-face card, multi-face card (types/subtypes aggregated), token returns `None`.
- **`test_card_set.py`** — `filter_format`, `filter_creatures`, `creature_type_counts` with small in-code card fixtures; invalid format raises `ValueError`.
- **`test_creature_types.py`** — end-to-end with a small in-memory AtomicCards fixture; verify TSV output contents and sort order.

No network calls in tests.

---

## Out of Scope (Next Phase)

- Plots / visualizations of creature type distribution
- Filtering by additional criteria (color, mana cost, set)
