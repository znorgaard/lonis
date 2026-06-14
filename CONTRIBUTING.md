# Contributing

## Development

```bash
uv sync --dev
uv run poe fix-and-check-all   # Fix then check everything
uv run poe check-all           # Check format, lint, types, and tests
uv run poe fix-all             # Auto-fix formatting and linting
```

## Adding a new tool

1. Create `lonis/tools/<name>.py` with a keyword-only function and a Google-style docstring.
2. Import and add it to `_tools` in `lonis/main.py`.

```bash
lonis <tool-name> --arg value
```
