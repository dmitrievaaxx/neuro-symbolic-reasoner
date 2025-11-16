import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, BotCommandScopeDefault
from dotenv import load_dotenv

from bot.handlers import router


# Настройка логирования
def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )


# Загрузка конфигурации из переменных окружения
def load_config() -> str:
    load_dotenv()
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set in environment")
    return token


# Установка команд бота для отображения в меню
async def setup_bot_commands(bot: Bot) -> None:
    commands = [
        BotCommand(command="start", description="Начать работу с ботом"),
        BotCommand(command="help", description="Помощь по использованию бота"),
    ]
    await bot.set_my_commands(commands, scope=BotCommandScopeDefault())
    
    try:
        installed_commands = await bot.get_my_commands(scope=BotCommandScopeDefault())
        logging.info(f"Команды бота установлены: {[cmd.command for cmd in installed_commands]}")
    except Exception as e:
        logging.warning(f"Не удалось проверить установленные команды: {e}")


async def main() -> None:
    setup_logging()
    token = load_config()

    bot = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    # Устанавливаем команды для автодополнения
    await setup_bot_commands(bot)
    
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())


