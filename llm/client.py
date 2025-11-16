import os
from typing import Callable, Awaitable, Any
from functools import lru_cache

from dotenv import load_dotenv
from openai import AsyncOpenAI, APIError

from llm.resolver import resolution_proof


load_dotenv()


MODELS = [
    "meta-llama/llama-3.3-70b-instruct:free",
    "deepseek/deepseek-r1-0528-qwen3-8b:free",
]


# Загрузка промпта для указанного модуля (formalizer, explainer)
@lru_cache(maxsize=3)
def _get_prompt(module: str) -> str:
    prompts_dir = os.path.join(os.path.dirname(__file__), "prompts")
    prompt_path = os.path.join(prompts_dir, f"{module}.txt")
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        raise RuntimeError(f"Промпт для модуля '{module}' не найден: {prompt_path}")


# Загрузка системного промпта (legacy, для обратной совместимости)
@lru_cache(maxsize=1)
def _get_system_prompt() -> str:
    prompt_path = os.path.join(os.path.dirname(__file__), "system_prompt.txt")
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return (
            "You are a helpful assistant answering in Russian by default. "
            "Give concise and clear answers."
        )


# Создание клиента OpenAI для работы с OpenRouter
@lru_cache(maxsize=1)
def _get_client() -> AsyncOpenAI:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is not set in environment")

    return AsyncOpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
    )


# Вызов LLM с механизмом fallback (если одна модель не работает, пробует следующую)
async def _call_llm(system_prompt: str, user_text: str, user_id: str | None = None) -> str:
    client = _get_client()

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_text},
    ]

    extra_headers = {}
    if user_id:
        extra_headers["X-Title"] = f"tg-user-{user_id}"

    last_error = None

    # Пробуем модели по очереди до первой успешной
    for model in MODELS:
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                extra_headers=extra_headers or None,
            )

            choice = response.choices[0]
            content = choice.message.content or ""
            return content.strip()

        except APIError as e:
            last_error = e
            continue
        except Exception as e:
            last_error = e
            continue

    if last_error:
        raise RuntimeError(
            f"Все модели ({', '.join(MODELS)}) не смогли обработать запрос. "
            f"Последняя ошибка: {last_error}"
        ) from last_error

    raise RuntimeError("Список моделей пуст")


# Модуль 1: Формализатор - преобразует текст задачи в формулы логики предикатов
async def module1_formalize(user_text: str, user_id: str | None = None) -> str:
    system_prompt = _get_prompt("formalizer")
    return await _call_llm(system_prompt, user_text, user_id)


# Модуль 2: Движок резолюций - выполняет алгоритм резолюций для поиска противоречия
async def module2_resolve(formulas_str: str) -> tuple[bool, list[str]]:
    formulas = [f.strip() for f in formulas_str.split(',') if f.strip()]
    return resolution_proof(formulas)


# Модуль 3: Объяснятор - преобразует формальный лог доказательства в понятное объяснение
async def module3_explain(proof_log: list[str], user_id: str | None = None) -> str:
    system_prompt = _get_prompt("explainer")
    log_text = "\n".join(proof_log)
    return await _call_llm(system_prompt, log_text, user_id)


# Полный пайплайн: Модуль 1 → Модуль 2 → Модуль 3
async def full_pipeline(
    user_text: str, 
    user_id: str | None = None,
    progress_callback: Callable[[str], Awaitable[Any]] | None = None
) -> dict[str, str | list[str] | bool]:
    if progress_callback:
        await progress_callback("🔷 Модуль 1: Формализация задачи...")
    formalized = await module1_formalize(user_text, user_id)
    
    # Модуль 2: Резолюции
    if progress_callback:
        await progress_callback("🔷 Модуль 2: Выполнение доказательства...")
    proof_found, proof_log = await module2_resolve(formalized)
    
    # Модуль 3: Объяснение
    if progress_callback:
        await progress_callback("🔷 Модуль 3: Формирование объяснения...")
    explanation = await module3_explain(proof_log, user_id)
    
    return {
        'formalized': formalized,
        'proof_found': proof_found,
        'proof_log': proof_log,
        'explanation': explanation
    }


# Legacy функция для обратной совместимости (использует полный пайплайн)
async def generate_reply(user_text: str, user_id: str | None = None) -> str:
    result = await full_pipeline(user_text, user_id)
    return result['explanation']


