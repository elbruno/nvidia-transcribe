FROM pytorch/pytorch:2.4.0-cuda12.1-cudnn9-runtime

WORKDIR /app

# Install system dependencies (libopus for audio, build tools for Python packages, curl for health checks)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libopus0 \
        libopus-dev \
        gcc \
        g++ \
        make \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Copy files first to allow better layer caching
COPY third_party/moshi /app/third_party/moshi
COPY moshi/start_moshi.sh /app/start_moshi.sh

# Combine pip operations to reduce layers and build time
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir /app/third_party/moshi && \
    pip install --no-cache-dir \
        opentelemetry-api==1.39.1 \
        opentelemetry-sdk==1.39.1 \
        opentelemetry-exporter-otlp==1.39.1 \
        opentelemetry-instrumentation-aiohttp-server==0.60b1 \
        opentelemetry-instrumentation-aiohttp-client==0.60b1 && \
    chmod +x /app/start_moshi.sh && \
    mkdir -p /ssl

# Set environment variables
ENV HF_HOME=/root/.cache/huggingface \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

EXPOSE 8998

# Health check using curl (Aspire also monitors via WithHttpHealthCheck)
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8998/health || exit 1

CMD ["/app/start_moshi.sh"]
