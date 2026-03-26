# ============================================================
# TripJoy AI Service — Dockerfile
# Multi-stage build for lean production image
# Base: Python 3.12-slim (~150MB vs ~1GB full)
# ============================================================

# ---- Stage 1: Builder ----
# Install dependencies in a separate layer to leverage Docker cache
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build tools needed by some packages (ortools, etc.)
# then clean up in the same layer to reduce image size
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (Docker cache layer)
COPY requirements.txt .

# Install to a local path (not system) for clean copy
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ---- Stage 2: Runtime ----
FROM python:3.12-slim AS runtime

WORKDIR /app

# Tạo non-root user cho bảo mật
RUN addgroup --system aiservice && adduser --system --group aiservice

# Copy installed packages từ builder stage
COPY --from=builder /install /usr/local

# Copy source code
COPY src/ ./src/

# Set permissions
RUN chown -R aiservice:aiservice /app
USER aiservice

# Environment defaults (override via docker-compose hoặc Kubernetes secret)
ENV PYTHONPATH=/app/src \
    APP_HOST=0.0.0.0 \
    APP_PORT=8000 \
    APP_RELOAD=false \
    LOG_LEVEL=INFO

EXPOSE 8000

# Healthcheck: gọi FastAPI /health endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Chạy với uvicorn production mode (không reload, workers=1 vì AI service stateless)
CMD ["python", "-m", "uvicorn", "travel_agent.api.server:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "1", \
     "--log-level", "info"]
