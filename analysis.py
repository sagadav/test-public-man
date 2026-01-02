import os
from mistralai import Mistral
from dotenv import load_dotenv

load_dotenv()

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

async def analyze_with_mistral(entries_text):
    if not MISTRAL_API_KEY:
        return "Ошибка: MISTRAL_API_KEY не найден."
    
    client = Mistral(api_key=MISTRAL_API_KEY)
    
    prompt = f"""
    Ты - эмпатичный психолог-аналитик, работающий в подходе КПТ.
    Проанализируй следующие записи о срывах пользователя:
    
    {entries_text}
    
    Дай краткую сводку, выдели основные паттерны (триггеры, места, эмоции) и дай 1-2 конкретных, мягких рекомендации.
    Не используй сложные термины, пиши дружелюбно. Пиши так будто обращаешся к самому пользователю.

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

async def generate_clarifying_question(goal_text):
    if not MISTRAL_API_KEY:
        return "Чтобы ясно понять результат: какой один документ или решение должно быть готово к концу этих 2 часов?"
    
    client = Mistral(api_key=MISTRAL_API_KEY)
    
    prompt = f"""
    Пользователь поставил себе цель на завтра: "{goal_text}".
    
    Твоя задача - задать ОДИН уточняющий вопрос, который поможет пользователю определить максимально конкретный, осязаемый результат (outcome). 
    Вопрос должен быть в стиле: Чтобы ясно понять результат: какой один документ или решение должно быть готово к концу дня?
    
    Пиши кратко, эмпатично и профессионально. Не пиши лишнего текста, только вопрос. Пиши на русском.
    Проверь свою грамматику и орфографию.

    Структура ответа:
    1. Уточняющий вопрос
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
        print(f"Mistral error: {e}")
        return "Чтобы ясно понять результат: какой один документ или решение должно быть готово к концу этих 2 часов?"

async def brainstorm_goal_failure(goal_text, result_text, reason):
    if not MISTRAL_API_KEY:
        return "Ничего страшного. Завтра будет новый шанс!"
    
    client = Mistral(api_key=MISTRAL_API_KEY)
    
    prompt = f"""
    Пользователь не выполнил свою топ-цель на сегодня.
    Цель: "{goal_text}"
    Ожидаемый результат: "{result_text}"
    Причина невыполнения: "{reason}"
    
    Ты - опытный коуч по продуктивности. Твоя задача - провести краткий брейншторм и дать ОДИН самый ценный, контекстный совет, который поможет избежать этой помехи завтра.
    
    Используй следующие ментальные модели:
    - Если помеха "срочные задачи" -> советуй "защищенное время" (time blocking).
    - Если помеха "сложно начать" -> советуй разбить на 15-минутный первый шаг или метод Pomodoro.
    - Если помеха "усталость" -> советуй пересмотреть масштаб цели или выбрать время с пиком энергии.
    - Если причина другая -> дай глубокий инсайт на основе КПТ или тайм-менеджмента.
    
    Пиши кратко (3-4 предложения), эмпатично и по делу. Без воды.
    """
    
    try:
        chat_response = await client.chat.complete_async(
            model="mistral-medium",
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                },
            ]
        )
        return chat_response.choices[0].message.content
    except Exception as e:
        print(f"Mistral brainstorm error: {e}")
        return "Ничего страшного. Попробуй проанализировать, что именно пошло не так, и завтра сделай шаг поменьше."
