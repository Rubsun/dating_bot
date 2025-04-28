FROM python:3.12-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

ADD pyproject.toml pyproject.toml
ADD uv.lock uv.lock

RUN uv sync --frozen --no-cache
ADD . .
