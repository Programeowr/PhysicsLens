# `app/main.py` — FastAPI Application Entry Point

## What It Does
Creates and configures the main FastAPI application instance. Sets up CORS, rate limiting, logging, health checks, and registers all route modules.

## Why It Exists
This is the single entry point that `uvicorn` loads. It wires together all components (routes, middleware, error handlers) into a running application.

## How It Works

### Initialization Flow
1. Creates `FastAPI()` instance
2. Adds `CORSMiddleware` — allows all origins (for local frontend dev)
3. Creates `slowapi.Limiter` with `get_remote_address` key function
4. Attaches limiter to app state and registers rate limit error handler
5. Configures `logging` based on `settings.debug`
6. Registers parse routes (`/parse`, `/parse-image`)
7. Registers diagram routes (`/diagram`, `/test-diagram/*`)

### Endpoints
- `GET /` — returns app info, version, and available endpoints
- `GET /health` — simple health check returning `200 OK`

### Running
```bash
uvicorn app.main:app --reload        # development
uvicorn app.main:app --host 0.0.0.0  # production
```

## Dependencies
- `fastapi` — web framework
- `slowapi` — rate limiting middleware
- `app.config` — settings
- `app.routes.parse` — parse router
- `app.routes.diagram` — diagram router
