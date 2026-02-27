# `app/routes/parse.py` — Parse Endpoints

## What It Does
Exposes two API endpoints for parsing physics problems:
- `POST /parse` — accepts text input (JSON body)
- `POST /parse-image` — accepts image upload (multipart form data)

## Why It Exists
These are the main entry points for the application. They handle HTTP request/response, input validation, rate limiting, and error formatting — keeping this responsibility separate from the parsing logic.

## How It Works

### `POST /parse`
1. Receives JSON body: `{ "problem": "..." }`
2. Validates via `ProblemInput` model (min 10 chars)
3. Calls `parse_physics_problem()` from the parser module
4. Returns `{ "status": "success", "data": {...} }`
5. On `ParsingError`: returns 422 with error details
6. On unexpected error: returns 500

### `POST /parse-image`
1. Receives multipart file upload (field: `file`)
2. Validates file type (JPEG, PNG, WebP, GIF, BMP)
3. Validates file size (max 10MB)
4. Calls `parse_physics_image()` from the parser module
5. Returns same response format as `/parse`

### Rate Limiting
Both endpoints are decorated with `@limiter.limit(settings.rate_limit)` using `slowapi`. Default: 10 requests/minute per IP address.

## Dependencies
- `fastapi` — routing, request handling, file uploads
- `slowapi` — rate limiting
- `app.parser` — parsing functions
- `app.models` — input validation
- `app.config` — rate limit setting

---

# `app/routes/diagram.py` — Diagram Endpoints

## What It Does
Exposes endpoints for generating SVG diagrams from parsed physics data, plus test endpoints for quick visual verification.

## Why It Exists
Separates diagram generation routing from the actual SVG generation logic. Also provides test endpoints so diagrams can be verified without needing the AI parser.

## How It Works

### `POST /diagram`
1. Receives parsed physics data as JSON body
2. Auto-detects diagram type based on surface types:
   - `inclined_plane` → incline generator
   - `pulley` → pulley generator
   - Contains "elevator" keywords → vertical generator
   - Default → horizontal generator
3. Returns SVG as `text/html` content type

### `GET /test-diagram`
Returns a hardcoded incline example SVG for quick testing.

### `GET /test-diagram/horizontal`, `/pulley`, `/vertical`
Return hardcoded example SVGs for each diagram type.

## Dependencies
- `fastapi` — routing
- `app.diagrams.*` — all 4 diagram generators
