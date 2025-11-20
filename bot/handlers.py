import asyncio

from aiogram import Bot, Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.enums import ChatAction

from llm.client import full_pipeline


router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    text = (
        "Привет! Я бот для логических доказательств.\n\n"
        "Я работаю в режиме полного пайплайна:\n"
        "🔷 Модуль 1: Формализация (перевод задачи на язык логики)\n"
        "🔷 Модуль 2: Движок резолюций (строгое доказательство)\n"
        "🔷 Модуль 3: Объяснение (перевод доказательства на русский)\n\n"
        "Просто отправь мне задачу на естественном языке, например:\n"
        "\"Сократ — человек. Все люди смертны. Докажи, что Сократ смертен.\"\n\n"
        "Доступные команды:\n"
        "/start — краткая информация\n"
        "/help — помощь по использованию бота"
    )
    await message.answer(text)


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    text = (
        "Я бот для логических доказательств с использованием нейро-символьного подхода.\n\n"
        "Как я работаю:\n"
        "1. Формализую твою задачу в логику предикатов\n"
        "2. Выполняю строгое доказательство через алгоритм резолюций\n"
        "3. Объясняю доказательство простым языком\n\n"
        "Просто напиши задачу на естественном языке, и я проведу полный анализ.\n"
        "История диалога не сохраняется — каждый запрос обрабатывается отдельно."
    )
    await message.answer(text)


# Периодическая отправка индикатора печати в чат
async def _show_typing_indicator(bot: Bot, chat_id: int, stop_event: asyncio.Event) -> None:
    while not stop_event.is_set():
        await bot.send_chat_action(chat_id, ChatAction.TYPING)
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=4.0)
            break
        except asyncio.TimeoutError:
            continue


# Форматирование результата полного пайплайна для отправки пользователю
def _format_pipeline_result(result: dict) -> str:
    lines = []
    
    # Модуль 1: Формализация
    lines.append("🔷 **Модуль 1 (Формализация):**")
    lines.append("")
    # result['formalized'] теперь список строк - выводим построчно с номерами
    clauses = result['formalized']
    for i, clause in enumerate(clauses, 1):
        lines.append(f"{i}. {clause}")
    lines.append("")
    lines.append(f"Всего клауз: {len(clauses)}")
    lines.append("")
    
    # Модуль 2: Доказательство
    lines.append("🔷 **Модуль 2 (Движок резолюций):**")
    if result['proof_found']:
        lines.append("✅ Противоречие найдено! Доказательство существует.")
    else:
        lines.append("❌ Противоречие не найдено. Доказательство не удалось построить.")
    lines.append("")
    lines.append("**Лог шагов доказательства:**")
    lines.append("```")
    lines.extend(result['proof_log'])
    lines.append("```")
    lines.append("")
    
    # Модуль 3: Объяснение
    lines.append("🔷 **Модуль 3 (Объяснение):**")
    lines.append(result['explanation'])
    
    return "\n".join(lines)


@router.message()
async def handle_message(message: Message, bot: Bot) -> None:
    user_text = message.text or ""

    if not user_text.strip():
        await message.answer("Пожалуйста, отправь текстовое сообщение с задачей.")
        return

    # Запускаем индикатор печати в фоне
    stop_typing = asyncio.Event()
    typing_task = asyncio.create_task(_show_typing_indicator(bot, message.chat.id, stop_typing))
    
    # Сообщения о прогрессе (будем обновлять одно сообщение)
    progress_message = None
    
    # Callback для отправки промежуточных сообщений о прогрессе
    async def progress_callback(text: str) -> None:
        nonlocal progress_message
        if progress_message is None:
            progress_message = await message.answer(text)
        else:
            try:
                await progress_message.edit_text(text)
            except Exception:
                # Если не удалось отредактировать (например, сообщение слишком старое), отправляем новое
                progress_message = await message.answer(text)

    try:
        result = await full_pipeline(
            user_text=user_text, 
            user_id=str(message.from_user.id),
            progress_callback=progress_callback
        )
        formatted_result = _format_pipeline_result(result)
        
        # Удаляем сообщение о прогрессе перед отправкой результата
        if progress_message:
            try:
                await progress_message.delete()
            except Exception:
                pass  # Игнорируем ошибки удаления
    except Exception as e:
        # Останавливаем индикатор печати
        stop_typing.set()
        typing_task.cancel()
        try:
            await typing_task
        except asyncio.CancelledError:
            pass
        
        # Логируем ошибку для отладки, но пользователю показываем простое сообщение
        import logging
        logging.error(f"Ошибка в пайплайне: {e}", exc_info=True)
        await message.answer("Произошла ошибка при обработке задачи. Попробуй ещё раз позже.")
        return
    finally:
        # Останавливаем индикатор печати
        stop_typing.set()
        typing_task.cancel()
        try:
            await typing_task
        except asyncio.CancelledError:
            pass

    # Telegram имеет лимит на длину сообщения (4096 символов)
    # Если сообщение слишком длинное, разбиваем на части
    max_length = 4000  # Оставляем запас
    if len(formatted_result) <= max_length:
        await message.answer(formatted_result, parse_mode="None")
    else:
        # Разбиваем на части
        parts = []
        current_part = []
        current_length = 0
        
        for line in formatted_result.split('\n'):
            line_length = len(line) + 1  # +1 для \n
            if current_length + line_length > max_length and current_part:
                parts.append('\n'.join(current_part))
                current_part = [line]
                current_length = line_length
            else:
                current_part.append(line)
                current_length += line_length
        
        if current_part:
            parts.append('\n'.join(current_part))
        
        # Отправляем части по очереди
        for i, part in enumerate(parts, 1):
            if len(parts) > 1:
                header = f"**Часть {i} из {len(parts)}:**\n\n"
                await message.answer(header + part, parse_mode="None")
            else:
                await message.answer(part, parse_mode="None")
