FROM pytorch/pytorch:2.4.0-cuda12.1-cudnn9-runtime

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends libopus0 libopus-dev \
    && rm -rf /var/lib/apt/lists/*

COPY third_party/moshi /app/third_party/moshi
COPY moshi/start_moshi.sh /app/start_moshi.sh
RUN pip install --no-cache-dir --upgrade pip \
    && pip install /app/third_party/moshi \
    && chmod +x /app/start_moshi.sh

RUN mkdir -p /ssl

ENV HF_HOME=/root/.cache/huggingface

EXPOSE 8998

CMD ["/app/start_moshi.sh"]
