# `app/config.py` — Application Configuration

## What It Does
Centralizes all application settings into a single `Settings` class, loading values from environment variables and the `.env` file.

## Why It Exists
Avoids hardcoded values scattered across the codebase. Provides a single source of truth for API keys, rate limits, model selection, and debug flags. Ensures the app fails fast if required config (like `GEMINI_API_KEY`) is missing.

## How It Works
Uses **pydantic-settings** `BaseSettings` with a nested `model_config` that reads from the `.env` file. A singleton `settings` instance is created at module level and imported wherever config is needed.

### Key Settings
| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `GEMINI_API_KEY` | `str` | *required* | Google Gemini API key |
| `RATE_LIMIT` | `str` | `"10/minute"` | Parse endpoint rate limit |
| `DEBUG` | `bool` | `False` | Enable debug logging |
| `GEMINI_MODEL` | `str` | `"gemini-2.5-flash"` | Which Gemini model to use |

## Dependencies
- `pydantic-settings` — loads env vars into typed Python objects
- `python-dotenv` — reads `.env` file (used internally by pydantic-settings)
