import pytest

from llm.client import _get_system_prompt, MODELS


def test_system_prompt_not_empty():
    prompt = _get_system_prompt()
    assert isinstance(prompt, str)
    assert prompt.strip() != ""


def test_models_list_not_empty():
    """Проверка, что список моделей для fallback не пустой."""
    assert isinstance(MODELS, list)
    assert len(MODELS) > 0
    assert all(isinstance(model, str) and model.strip() for model in MODELS)


@pytest.mark.asyncio
async def test_generate_reply_signature():
    """
    Базовая проверка: функция существует и является awaitable.

    Здесь мы не вызываем реальное API, а лишь проверяем,
    что сигнатура и типы корректны. Для реального интеграционного
    теста потребуется замокать клиент OpenAI/OpenRouter.
    """
    from llm.client import generate_reply

    coro = generate_reply("тестовый вопрос", user_id="123")
    assert hasattr(coro, "__await__")


