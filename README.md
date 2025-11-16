## Telegram бот с LLM (OpenRouter)

Простой Telegram‑бот на `aiogram`, который отвечает на вопросы пользователя с помощью LLM через OpenRouter (OpenAI‑совместимый клиент).

### Стек

- **Язык**: Python
- **Telegram API**: `aiogram` (v3)
- **LLM API**: OpenRouter через `openai` client
- **Тесты**: `pytest`
- **Управление зависимостями**: `uv`
- **Деплой**: Docker

### Структура проекта

- `bot/`
  - `main.py` — точка входа, запуск бота
  - `handlers.py` — обработчики команд и сообщений
- `llm/`
  - `client.py` — обёртка для вызова OpenRouter
  - `system_prompt.txt` — системный промпт для LLM
- `tests/`
  - `test_bot.py` — базовые тесты
- `doc/` — документация продукта

### Переменные окружения

Создайте файл `.env` в корне проекта и укажите:

```text
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

**Примечание**: Модель LLM выбирается автоматически из списка в `llm/client.py` с механизмом fallback. Если первая модель не работает, бот автоматически пробует следующую из списка.

### Установка и запуск (локально)

1. Установите зависимости:

```bash
uv sync
```

2. Запустите бота:

```bash
python -m bot.main
```

### Тесты

```bash
pytest -q
```

### Docker

Сборка и запуск:

```bash
docker build -t neuro-symbolic-bot .
docker run --rm --env-file .env neuro-symbolic-bot
```


