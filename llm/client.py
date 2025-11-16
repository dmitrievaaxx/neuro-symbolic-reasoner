import os
from functools import lru_cache

from dotenv import load_dotenv
from openai import AsyncOpenAI, APIError

from llm.resolver import resolution_proof


load_dotenv()


MODELS = [
    "meta-llama/llama-3.3-70b-instruct:free",
    "deepseek/deepseek-r1-0528-qwen3-8b:free",
]


@lru_cache(maxsize=3)
def _get_prompt(module: str) -> str:
    """
    Загружает промпт для указанного модуля.
    
    Args:
        module: 'formalizer', 'explainer'
    
    Returns:
        Текст промпта
    """
    prompts_dir = os.path.join(os.path.dirname(__file__), "prompts")
    prompt_path = os.path.join(prompts_dir, f"{module}.txt")
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        raise RuntimeError(f"Промпт для модуля '{module}' не найден: {prompt_path}")


@lru_cache(maxsize=1)
def _get_system_prompt() -> str:
    """Load system prompt from file (legacy, для обратной совместимости)."""
    prompt_path = os.path.join(os.path.dirname(__file__), "system_prompt.txt")
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        # Fallback на очень простой системный промпт
        return (
            "You are a helpful assistant answering in Russian by default. "
            "Give concise and clear answers."
        )


@lru_cache(maxsize=1)
def _get_client() -> AsyncOpenAI:
    """Create AsyncOpenAI client configured for OpenRouter."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is not set in environment")

    return AsyncOpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
    )


async def _call_llm(system_prompt: str, user_text: str, user_id: str | None = None) -> str:
    """
    Вспомогательная функция для вызова LLM.
    
    Использует механизм fallback: если одна модель не работает, пробует следующую.
    """
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


async def module1_formalize(user_text: str, user_id: str | None = None) -> str:
    """
    Модуль 1: Формализатор.
    
    Преобразует текст задачи на естественном языке в набор формул логики предикатов.
    
    Returns:
        Строка с формулами, разделенными запятыми
    """
    system_prompt = _get_prompt("formalizer")
    return await _call_llm(system_prompt, user_text, user_id)


async def module2_resolve(formulas_str: str) -> tuple[bool, list[str]]:
    """
    Модуль 2: Движок резолюций.
    
    Принимает строку с формулами, разделенными запятыми.
    Выполняет алгоритм резолюций для поиска противоречия.
    
    Returns:
        Кортеж (найдено_противоречие, лог_шагов)
    """
    # Парсим формулы (разделяем по запятым)
    formulas = [f.strip() for f in formulas_str.split(',') if f.strip()]
    return resolution_proof(formulas)


async def module3_explain(proof_log: list[str], user_id: str | None = None) -> str:
    """
    Модуль 3: Объяснятор.
    
    Преобразует формальный лог шагов доказательства в понятное объяснение на русском.
    
    Args:
        proof_log: Список строк с логом шагов доказательства
        user_id: ID пользователя (для метаданных)
    
    Returns:
        Текст объяснения на русском языке
    """
    system_prompt = _get_prompt("explainer")
    log_text = "\n".join(proof_log)
    return await _call_llm(system_prompt, log_text, user_id)


async def full_pipeline(user_text: str, user_id: str | None = None) -> dict[str, str | list[str] | bool]:
    """
    Полный пайплайн: Модуль 1 → Модуль 2 → Модуль 3.
    
    Args:
        user_text: Текст задачи на естественном языке
        user_id: ID пользователя
    
    Returns:
        Словарь с результатами всех модулей:
        {
            'formalized': str,      # Результат Модуля 1
            'proof_found': bool,    # Результат Модуля 2
            'proof_log': list[str], # Лог шагов Модуля 2
            'explanation': str      # Результат Модуля 3
        }
    """
    # Модуль 1: Формализация
    formalized = await module1_formalize(user_text, user_id)
    
    # Модуль 2: Резолюции
    proof_found, proof_log = await module2_resolve(formalized)
    
    # Модуль 3: Объяснение
    explanation = await module3_explain(proof_log, user_id)
    
    return {
        'formalized': formalized,
        'proof_found': proof_found,
        'proof_log': proof_log,
        'explanation': explanation
    }


# Обратная совместимость
async def generate_reply(user_text: str, user_id: str | None = None) -> str:
    """
    Legacy функция для обратной совместимости.
    Теперь использует полный пайплайн.
    """
    result = await full_pipeline(user_text, user_id)
    return result['explanation']


