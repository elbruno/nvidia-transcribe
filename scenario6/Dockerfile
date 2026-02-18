FROM python:3.12-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends libopus0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
COPY third_party/moshi /app/third_party/moshi
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY app.py /app/app.py
COPY static /app/static

ENV APP_HOST=0.0.0.0
ENV APP_PORT=8010

EXPOSE 8010

CMD ["python", "/app/app.py"]
