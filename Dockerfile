FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Установим базовые утилиты (сертификаты и т.п.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Копируем файлы проекта (включая пакеты bot и llm)
COPY . .

# Устанавливаем зависимости и сам пакет по pyproject.toml
RUN pip install --no-cache-dir .

CMD ["python", "-m", "bot.main"]
