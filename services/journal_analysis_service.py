from services.mistral_client import get_mistral_client


async def analyze_with_mistral(entries_text):
    client = get_mistral_client()
    if not client:
        return "Ошибка: MISTRAL_API_KEY не найден."

    prompt = f"""
    Ты - эмпатичный психолог-аналитик, работающий в подходе КПТ.
    Проанализируй следующие записи о срывах пользователя:

    {entries_text}

    Дай краткую сводку, выдели основные паттерны (триггеры, места,
    эмоции) и дай 1-2 конкретных, мягких рекомендации.
    Не используй сложные термины, пиши дружелюбно.
    Пиши так будто обращаешся к самому пользователю.

    Структура ответа:
    Анализ на данный момент:
    1. Краткая сводка
    2. Основные паттерны (триггеры, места, эмоции)
    3. 1-2 конкретных, мягких рекомендации
    """

    try:
        chat_response = await client.chat.complete_async(
            model="mistral-tiny",
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                },
            ]
        )
        return chat_response.choices[0].message.content
    except Exception as e:
        return f"Ошибка при анализе: {e}"
