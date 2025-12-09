FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_HOME=/app \
    CONFIG_PATH=/app/config.yaml \
    SERVICE_NAME=tda-collector \
    ENVIRONMENT=dev

WORKDIR ${APP_HOME}

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r requirements-dev.txt

COPY src ./src
COPY config.yaml ./config.yaml

RUN useradd -m appuser && chown -R appuser:appuser ${APP_HOME}
USER appuser

ENV PYTHONPATH=${APP_HOME}/src

ENTRYPOINT ["python", "-m", "tda_collector"]
CMD ["--mode=live"]

