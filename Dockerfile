# LMArena Bridge backend container (FastAPI + Uvicorn)
# Builds a self-contained image that serves api_server:app on 5102
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    ALL_PROXY= \
    HTTP_PROXY= \
    HTTPS_PROXY= \
    NO_PROXY=127.0.0.1,localhost

WORKDIR /app

# Optional system deps (wheels are preferred; remove if not needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt && pip install "requests[socks]"

# Copy project
COPY . .

EXPOSE 5102

# Run FastAPI via uvicorn
CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "5102", "--workers", "1"]