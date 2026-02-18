FROM pytorch/pytorch:2.4.0-cuda12.1-cudnn9-runtime

WORKDIR /app

# Install system dependencies and build tools
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libopus0 \
        libopus-dev \
        gcc \
        g++ \
        make \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip first
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copy moshi package
COPY third_party/moshi /app/third_party/moshi

# Install moshi package (this includes its dependencies like aiohttp)
RUN pip install --no-cache-dir /app/third_party/moshi

# Install OpenTelemetry packages separately to avoid conflicts
RUN pip install --no-cache-dir \
    opentelemetry-api \
    opentelemetry-sdk \
    opentelemetry-exporter-otlp \
    opentelemetry-instrumentation-aiohttp-client

# Copy startup script and set permissions
COPY moshi/start_moshi.sh /app/start_moshi.sh
RUN chmod +x /app/start_moshi.sh

# Create SSL directory
RUN mkdir -p /ssl

# Set environment variables
ENV HF_HOME=/root/.cache/huggingface
ENV PYTHONUNBUFFERED=1

EXPOSE 8998

CMD ["/app/start_moshi.sh"]
