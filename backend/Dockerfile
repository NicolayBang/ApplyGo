FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY backend/pyproject.toml backend/alembic.ini ./
COPY backend/src ./src
COPY backend/alembic ./alembic
COPY backend/scripts ./scripts
COPY frontend ../frontend

RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir -e ".[dev]"
