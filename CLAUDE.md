# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`lonis` is a Python toolkit for analyzing Magic: The Gathering card data. It exposes a unified CLI where each sub-command is a plain Python function dispatched by [`defopt`](https://defopt.readthedocs.io/).

## Commands

All commands use `uv run --locked poe <task>`. Key tasks defined in `pyproject.toml`:

| Task | Purpose |
|---|---|
| `uv run --locked poe check-all` | Format check + lint + type check + tests (used in CI) |
| `uv run --locked poe fix-and-check-all` | Auto-fix format/lint, then type check + tests |
| `uv run --locked poe check-tests` | Run pytest only |
| `uv run --locked poe check-typing` | Run mypy only |
| `uv run --locked poe fix-all` | Auto-fix format and lint |

Run a single test file: `uv run --locked pytest tests/tools/test_creature_types.py`  
Run a single test: `uv run --locked pytest tests/tools/test_creature_types.py::test_creature_types_writes_correct_types`

## Architecture

### Adding a new tool

1. Create `lonis/tools/<name>.py` with a single top-level function.
2. Register it in `lonis/main.py`'s `_tools` list.
3. Update `README.md` to document the tool and its options.

`defopt` derives the CLI sub-command name and `--option` flags from the function name and typed keyword arguments. The function docstring (Google convention) provides the help text; `Args:` entries document individual flags.

Whenever a CLI tool is added or an existing tool's options change (a flag is added, removed, renamed, or its default changes), update `README.md` in the same change so its documented usage and options stay in sync.

### Test conventions

- Tests mirror the package structure under `tests/`.
- `tests/conftest.py` provides a `datadir` fixture pointing to `tests/data/` for file-based tests.
- Logging output is captured with `caplog`; assert against `caplog.text`.

## AtomicCards Data Schema

Card data is sourced from [mtgjson.com](https://mtgjson.com/data-models/card/card-atomic/) (`AtomicCards.json`), cached daily at `~/.cache/lonis/AtomicCards.json`. The top-level structure is a dict mapping card name → list of face objects (single-face cards have one element; multi-face cards have one per face).

### Always-present fields on each face

| Field | Type | Definition |
|---|---|---|
| `name` | `str` | Canonical English card name |
| `layout` | `str` | Print layout (`normal`, `transform`, `split`, `adventure`, `token`, …) |
| `type` | `str` | Full type line as printed (e.g. `"Legendary Creature — Elf Wizard"`) |
| `types` | `list[str]` | Main types extracted from the type line (e.g. `["Creature"]`) |
| `subtypes` | `list[str]` | Subtypes after the em-dash (e.g. `["Elf", "Wizard"]`) |
| `supertypes` | `list[str]` | Supertypes (e.g. `["Legendary"]`, `["Basic"]`, `["Snow"]`) |
| `colorIdentity` | `list[str]` | Color identity letters for Commander (`W`, `U`, `B`, `R`, `G`) |
| `colors` | `list[str]` | Colors the card actually is (not counting reminder text) |
| `manaValue` | `float` | Converted mana cost (canonical name; `convertedManaCost` is a legacy alias) |
| `convertedManaCost` | `float` | Legacy alias for `manaValue` |
| `legalities` | `dict[str, str]` | Format → legality string (`"Legal"`, `"Banned"`, `"Restricted"`, `"Not Legal"`) |
| `printings` | `list[str]` | Set codes where this card has appeared |
| `identifiers` | `dict` | Cross-reference IDs (Scryfall, TCGPlayer, etc.) |
| `foreignData` | `list[dict]` | Translated name/text per language |
| `purchaseUrls` | `dict` | Store purchase links (TCGPlayer, Cardmarket, etc.) |
| `isFunny` | `bool` | True for Un-set / silver-border / acorn cards |

### Conditional fields (only present when relevant)

| Field | When present | Definition |
|---|---|---|
| `manaCost` | Cards with a mana cost | Mana cost string (e.g. `"{2}{G}{G}"`) |
| `text` | Cards with rules text | Oracle rules text |
| `power` | Creatures and some artifacts | Power as string (e.g. `"3"`, `"*"`) |
| `toughness` | Creatures and some artifacts | Toughness as string |
| `loyalty` | Planeswalkers | Starting loyalty as string |
| `life` | Vanguard cards | Life modifier |
| `hand` | Vanguard cards | Hand size modifier |
| `keywords` | Cards with keyword abilities | List of keyword names (e.g. `["Flying", "Vigilance"]`) |
| `producedMana` | Mana-producing cards | Colors/types of mana this card can produce |
| `colorIndicator` | Cards with a color indicator dot | Colors from the color indicator (no mana cost) |
| `asciiName` | Cards with non-ASCII names | ASCII-safe version of `name` |
| `faceName` | Multi-face cards | Name of this specific face |
| `side` | Multi-face cards | Which face this is (`a`, `b`, `c`, …) |
| `faceConvertedManaCost` | Multi-face cards | CMC of this face only |
| `faceManaValue` | Multi-face cards | Mana value of this face only |
| `edhrecRank` | Cards tracked by EDHREC | Popularity rank (lower = more popular) |
| `edhrecSaltiness` | Cards tracked by EDHREC | How much opponents dislike seeing this card |
| `isReserved` | Reserved List cards | True if on the Reserved List |
| `isGameChanger` | High-impact cards | Marks format-warping cards |
| `leadershipSkills` | Potential commanders | Legality as a commander per format |
| `relatedCards` | Cards that reference others | Links to associated card names (tokens, etc.) |
| `rulings` | Cards with official rulings | List of `{date, text}` rulings |
| `subsets` | Cards in special subsets | Subset tags (e.g. Alchemy rebalances) |

### Fields currently used by `MtgCard`

`layout`, `types`, `subtypes`, `supertypes`, `colorIdentity`, `colors`, `convertedManaCost`, `legalities`, `isFunny`

## Scryfall API

A structured reference for the Scryfall REST API is at `docs/scryfall_api.md`. Read it into context when:
- Adding any tool that calls the Scryfall API (endpoints, parameters, field names, pagination).
- Working with color arrays, mana cost notation, or mana symbology.
- Implementing or reviewing any HTTP request logic targeting `api.scryfall.com`.
- Deciding whether to use a live API endpoint vs. bulk data download.

### API Rate Limits — Never Exceed

**CRITICAL: Exceeding rate limits can result in a permanent ban of this application.**

| Endpoint | Hard limit |
|---|---|
| `/cards/search`, `/cards/named`, `/cards/random`, `/cards/collection` | 2 requests/second |
| All other `api.scryfall.com` endpoints | 10 requests/second |

Rules:
- **Always use bulk data** (`GET /bulk-data`) instead of repeated API calls when looking up large numbers of cards, names, or images. Bulk files are served from `*.scryfall.io` with no rate limit.
- **Cache all API responses** for at least 24 hours before re-fetching.
- Never build loops that call card endpoints without deliberate per-request delays that respect the limits above.
- If an HTTP 429 is received, back off immediately and do not retry until the 30-second cooldown has elapsed.

## Code Style

- **Line length**: 100
- **Imports**: one import per line (`force-single-line = true` in isort)
- **Docstrings**: Google convention; required on all public functions/classes
- **Type hints**: strict mypy — all defs must be fully typed, `Any` is disallowed
- **Ruff**: linting and formatting; see `[tool.ruff.lint]` in `pyproject.toml` for enabled rule sets
- **Builtin shadowing (A002)**: avoid Python builtin names as parameter names (e.g. use `fmt` not `format`)
