# Terra Intelligence Engine — FastAPI backend
FROM python:3.12-slim AS base

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

FROM base AS deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM deps AS runtime
COPY . .

EXPOSE 8000
# Most PaaS platforms (Render, Railway, Heroku) inject a dynamic $PORT and
# require the container to listen on it; default to 8000 for local/compose use.
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
