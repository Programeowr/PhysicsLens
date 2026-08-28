# Multi-stage build for PhysicsLens backend
FROM python:3.14-slim as builder

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Final stage
FROM python:3.14-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY physics_diagram/ ./physics_diagram/

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/').raise_for_status()"

# Run the application
CMD ["uvicorn", "physics_diagram.api:app", "--host", "0.0.0.0", "--port", "8000"]
