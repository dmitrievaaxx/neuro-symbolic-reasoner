FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Установка uv
RUN pip install --no-cache-dir uv

COPY pyproject.toml ./

RUN uv sync --no-dev

COPY . .

CMD ["python", "-m", "bot.main"]


