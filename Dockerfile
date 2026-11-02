FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# The dashboard uses headless OpenCV. Camera, audio and ML extras stay
# opt-in for hardware-specific deployments.
COPY requirements-ci.txt ./
RUN python -m pip install --upgrade pip && \
    python -m pip install -r requirements-ci.txt

COPY . .

EXPOSE 5000
CMD ["python", "run.py", "web"]
