**Запуск**  
[@LogiSolveBot](https://t.me/LogiSolveBot)
1. Создать файл `.env` в корне проекта и указать:

```text
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
OPENROUTER_API_KEY=your_openrouter_api_key_here
```  

2. Создать и активировать виртуальное окружение  

```bash
python -m venv .venv
.\.venv\Scripts\activate
```

3. Установить зависимости  
```bash
uv sync
```

4. Запустить бота
```bash
python -m bot.main
```
