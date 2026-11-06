FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    VISIONER_LOG_DIR=/app/data/logs

WORKDIR /app

# The default web image intentionally excludes hardware-specific ML/audio stacks.
COPY requirements-ci.txt ./
RUN python -m pip install --upgrade pip && \
    python -m pip install -r requirements-ci.txt

COPY . .

RUN mkdir -p /app/data/logs /app/data/evidence && \
    useradd --create-home --uid 10001 appuser && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 5000
CMD ["gunicorn", "--workers", "2", "--threads", "4", "--timeout", "30", "--bind", "0.0.0.0:5000", "run:create_app()"]
