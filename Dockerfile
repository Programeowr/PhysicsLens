# Multi-stage build for PhysicsLens backend
FROM python:3.14-slim AS builder

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --user -r requirements.txt


# Final stage
FROM python:3.14-slim

WORKDIR /app

COPY --from=builder /root/.local /root/.local

COPY physics_diagram/ ./physics_diagram/

ENV PATH=/root/.local/bin:$PATH

EXPOSE 8000

# Railway-compatible health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["sh", "-c", "uvicorn physics_diagram.api:app --host 0.0.0.0 --port ${PORT:-8000}"]