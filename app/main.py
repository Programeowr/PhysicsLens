"""
PhysicsLens — FastAPI Application

Main entry point. Sets up CORS, rate limiting, and registers routes.
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.routes import parse, diagram

# ── Logging ──────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ── Rate Limiter ─────────────────────────────────────────────────────────

limiter = Limiter(key_func=get_remote_address)

# ── FastAPI App ──────────────────────────────────────────────────────────

app = FastAPI(
    title="PhysicsLens API",
    description="Parse physics problems and generate free body diagrams using AI.",
    version="0.2.0",
)

# Attach rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS — allow all origins during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register Routes ─────────────────────────────────────────────────────

app.include_router(parse.router, tags=["Parsing"])
app.include_router(diagram.router, tags=["Diagrams"])


# ── Health Check ─────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "app": "PhysicsLens",
        "version": "0.2.0",
        "status": "running",
        "endpoints": ["/parse", "/parse-image", "/diagram", "/test-diagram"],
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}
