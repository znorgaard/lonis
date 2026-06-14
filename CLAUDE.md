# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`lonis` is a Python toolkit for genetics and genomics analysis. It exposes a unified CLI where each sub-command is a plain Python function dispatched by [`defopt`](https://defopt.readthedocs.io/).

## Commands

All commands use `uv run --locked poe <task>`. Key tasks defined in `pyproject.toml`:

| Task | Purpose |
|---|---|
| `uv run --locked poe check-all` | Format check + lint + type check + tests (used in CI) |
| `uv run --locked poe fix-and-check-all` | Auto-fix format/lint, then type check + tests |
| `uv run --locked poe check-tests` | Run pytest only |
| `uv run --locked poe check-typing` | Run mypy only |
| `uv run --locked poe fix-all` | Auto-fix format and lint |

Run a single test file: `uv run --locked pytest tests/tools/test_hello.py`  
Run a single test: `uv run --locked pytest tests/tools/test_hello.py::test_hello_default`

## Architecture

### Adding a new tool

1. Create `lonis/tools/<name>.py` with a single top-level function.
2. Register it in `lonis/main.py`'s `_tools` list.

`defopt` derives the CLI sub-command name and `--option` flags from the function name and typed keyword arguments. The function docstring (Google convention) provides the help text; `Args:` entries document individual flags.

### Test conventions

- Tests mirror the package structure under `tests/`.
- `tests/conftest.py` provides a `datadir` fixture pointing to `tests/data/` for file-based tests.
- Logging output is captured with `caplog`; assert against `caplog.text`.

## Code Style

- **Line length**: 100
- **Imports**: one import per line (`force-single-line = true` in isort)
- **Docstrings**: Google convention; required on all public functions/classes
- **Type hints**: strict mypy — all defs must be fully typed, `Any` is disallowed
- **Ruff**: linting and formatting; see `[tool.ruff.lint]` in `pyproject.toml` for enabled rule sets
