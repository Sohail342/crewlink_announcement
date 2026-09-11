FROM python:3.13-slim

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN pip install --no-cache-dir uv && uv sync --frozen --no-dev

COPY . .

ENV PYTHONUNBUFFERED=1
CMD ["uv", "run", "celery", "-A", "config", "worker", "-l", "info"]