# `app/parser.py` — AI Parsing Engine

## What It Does
Orchestrates the full parsing pipeline: sends physics problems (text or image) to Google Gemini, retries on failures, parses the JSON response, and validates it against the Pydantic models.

## Why It Exists
The Gemini API can fail transiently (network issues, rate limits). This module wraps it with:
- **Retry logic** — 3 attempts with exponential backoff
- **JSON parsing** with clear error messages
- **Pydantic validation** to catch schema violations
- **Custom exception** (`ParsingError`) for the routes to handle

## How It Works

### `_call_gemini(prompt)`
Calls the Gemini text API with `temperature=0` (deterministic output) and `response_mime_type="application/json"` to force JSON output. Decorated with `@retry` for 3 attempts on `ConnectionError` / `TimeoutError`.

### `_call_gemini_with_image(prompt, image_bytes, mime_type)`
Multimodal variant — sends both the image and prompt text to Gemini Vision using `types.Part.from_bytes()`. Same retry logic.

### `_validate_parsed_output(raw_text)`
Shared validation logic:
1. `json.loads()` — parse raw text to dict
2. `ParsedPhysicsProblem.model_validate()` — validate against Pydantic schema
3. Raises `ParsingError` with the raw output attached for debugging

### `parse_physics_problem(problem_text)`
Public API for text problems: builds prompt → calls Gemini → validates.

### `parse_physics_image(image_bytes, mime_type)`
Public API for image problems: builds image prompt → calls Gemini Vision → validates.

### `ParsingError`
Custom exception that carries:
- `message` — human-readable error
- `raw_output` — the raw AI response (for debugging)

## Dependencies
- `google-genai` — Google Gemini API client
- `tenacity` — retry decorator with exponential backoff
- `app.models` — Pydantic validation models
- `app.prompts` — prompt builders
- `app.config` — API key and model settings
