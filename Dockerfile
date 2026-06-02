FROM python:3.12.10-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev

COPY src/ src/

ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

CMD ["uv", "run", "--no-dev", "uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8000"]
