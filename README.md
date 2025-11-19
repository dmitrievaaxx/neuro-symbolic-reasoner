**Запуск**  
[@LogiSolveBot](https://t.me/LogiSolveBot)

1. Склонировать репозиторий и перейти в папку
```
git clone https://github.com/dmitrievaaxx/neuro-symbolic-reasoner
cd neuro-symbolic-reasoner/
```   
2. Создать файл `.env` в корне проекта и указать:
```text
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
OPENROUTER_API_KEY=your_openrouter_api_key_here
```  
3. Создать и активировать виртуальное окружение  
```
python -m venv .venv
.\.venv\Scripts\activate
```
4. Установить зависимости  
```
pip install uv
uv sync
```
5. Запустить бота
```
python -m bot.main
```
