# ============================================================
# Stage 1: Builder — compile native extensions, resolve deps
# ============================================================
ARG BASE_IMAGE=nvidia/cuda:12.4.1-runtime-ubuntu22.04
FROM ${BASE_IMAGE} AS builder

# Fast Rust-based package manager (deterministic, lockfile-friendly)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Build tools needed for compiling native extensions (sphn, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        pkg-config \
        libopus-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY third_party/moshi /app/third_party/moshi

# Install Python 3.12 to a predictable path, create venv, install all deps
ENV UV_PYTHON_INSTALL_DIR=/opt/python
RUN uv venv /app/.venv --python 3.12 && \
    uv pip install --python /app/.venv/bin/python \
        torch==2.4.1 --index-url https://download.pytorch.org/whl/cu124 && \
    uv pip install --python /app/.venv/bin/python \
        /app/third_party/moshi \
        opentelemetry-api==1.39.1 \
        opentelemetry-sdk==1.39.1 \
        opentelemetry-exporter-otlp==1.39.1 \
        opentelemetry-instrumentation-aiohttp-server==0.60b1 \
        opentelemetry-instrumentation-aiohttp-client==0.60b1

# ============================================================
# Stage 2: Runtime — lean final image, no build tools
# ============================================================
FROM ${BASE_IMAGE}

# Runtime-only: libopus shared lib + curl for health checks
RUN apt-get update && apt-get install -y --no-install-recommends \
        libopus0 \
        curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy Python runtime and virtual environment from builder
COPY --from=builder /opt/python /opt/python
COPY --from=builder /app/.venv /app/.venv

COPY moshi/start_moshi.sh /app/start_moshi.sh
RUN chmod +x /app/start_moshi.sh && mkdir -p /ssl

ENV PATH="/app/.venv/bin:$PATH" \
    HF_HOME=/root/.cache/huggingface \
    PYTHONUNBUFFERED=1

EXPOSE 8998

# Health check using curl (Aspire also monitors via WithHttpHealthCheck)
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8998/health || exit 1

CMD ["/app/start_moshi.sh"]
