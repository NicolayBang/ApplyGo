FROM node:20-slim AS frontend-build

WORKDIR /app/frontend/app

COPY frontend/app/package*.json ./
RUN npm ci

COPY frontend/app ./
RUN npm run build

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY backend/pyproject.toml backend/alembic.ini ./
COPY backend/src ./src
COPY backend/alembic ./alembic
COPY backend/scripts ./scripts
COPY --from=frontend-build /app/frontend/dist ../frontend/dist

RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir -e ".[dev]"
