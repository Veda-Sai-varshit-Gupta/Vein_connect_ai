# ── VeinConnect AI — Backend Dockerfile ──────────────────────────────────────
# Multi-stage build: builder installs deps, final image is slim

# Stage 1: Builder
FROM python:3.12-slim AS builder

WORKDIR /app

# Install system dependencies for asyncpg + bcrypt compilation
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies into a venv
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Stage 2: Final
FROM python:3.12-slim AS final

WORKDIR /app

# Runtime deps only
RUN apt-get update && apt-get install -y \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Create non-root user for security
RUN addgroup --system veinconnect && adduser --system --group veinconnect
USER veinconnect

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health').raise_for_status()"

# Run with uvicorn using the PORT environment variable (default to 8000 if not set)
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 2
