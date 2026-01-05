import json
import re
from services.mistral_client import get_mistral_client


async def generate_clarifying_question(goal_text):
    client = get_mistral_client()
    if not client:
        return (
            "Чтобы ясно понять результат: какой один документ или "
            "решение должно быть готово к концу этих 2 часов?"
        )

    prompt = f"""
    Пользователь поставил себе цель на завтра: "{goal_text}".

    Твоя задача - задать ОДИН уточняющий вопрос, который поможет
    пользователю определить максимально конкретный, осязаемый
    результат (outcome).
    Вопрос должен быть в стиле: Чтобы ясно понять результат: какой
    один документ или решение должно быть готово к концу дня?

    Пиши кратко, эмпатично и профессионально. Не пиши лишнего текста,
    только вопрос. Пиши на русском.
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
        return (
            "Чтобы ясно понять результат: какой один документ или "
            "решение должно быть готово к концу этих 2 часов?"
        )


async def brainstorm_goal_failure(goal_text, result_text, reason):
    client = get_mistral_client()
    if not client:
        return "Ничего страшного. Завтра будет новый шанс!"
    
    prompt = f"""
    Пользователь не выполнил свою топ-цель на сегодня.
    Цель: "{goal_text}"
    Ожидаемый результат: "{result_text}"
    Причина невыполнения: "{reason}"

    Ты - опытный коуч по продуктивности. Твоя задача - провести
    краткий брейншторм и дать ОДИН самый ценный, контекстный совет,
    который поможет избежать этой помехи завтра.

    Используй следующие ментальные модели:
    - Если помеха "срочные задачи" -> советуй "защищенное время"
      (time blocking).
    - Если помеха "сложно начать" -> советуй разбить на 15-минутный
      первый шаг или метод Pomodoro.
    - Если помеха "усталость" -> советуй пересмотреть масштаб цели
      или выбрать время с пиком энергии.
    - Если причина другая -> дай глубокий инсайт на основе КПТ
      или тайм-менеджмента.

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
        return (
            "Ничего страшного. Попробуй проанализировать, что именно "
            "пошло не так, и завтра сделай шаг поменьше."
        )


async def analyze_goals_list(goals_list):
    """
    Анализирует список целей и определяет топ-цель дня,
    а также анализирует каждую цель по SMART.

    Args:
        goals_list: Список целей. Может быть списком строк или
                   списком объектов GoalEntry.
                   Если это GoalEntry, используется goal_text.

    Returns:
        dict: {
            'top_goal': {
                'goal': str,  # Текст топ-цели
                'reason': str  # Обоснование, почему это топ-цель
            },
            'smart_analysis': [
                {
                    'goal': str,  # Текст цели
                    'smart': {
                        'specific': {'score': int, 'comment': str},
                        # 0-10, комментарий
                        'measurable': {'score': int, 'comment': str},
                        'achievable': {'score': int, 'comment': str},
                        'relevant': {'score': int, 'comment': str},
                        'time_bound': {'score': int, 'comment': str}
                    },
                    'overall_score': int,  # Средний балл SMART (0-10)
                    'recommendations': str  # Рекомендации по улучшению
                }
            ]
        }
    """
    client = get_mistral_client()
    if not client:
        return {
            'top_goal': {
                'goal': goals_list[0] if goals_list else '',
                'reason': 'Анализ недоступен: MISTRAL_API_KEY не найден.'
            },
            'smart_analysis': []
        }
    
    goals_text_list = []
    for goal in goals_list:
        if isinstance(goal, str):
            goals_text_list.append(goal)
        else:
            goals_text_list.append(goal.goal_text)
    
    if not goals_text_list:
        return {
            'top_goal': {'goal': '', 'reason': 'Список целей пуст.'},
            'smart_analysis': []
        }
    
    goals_formatted = "\n".join([
        f"{i+1}. {goal}" for i, goal in enumerate(goals_text_list)
    ])
    
    prompt = f"""
    Ты - опытный коуч по продуктивности и тайм-менеджменту. Проанализируй список целей пользователя и выполни две задачи:

    СПИСОК ЦЕЛЕЙ:
    {goals_formatted}

    ЗАДАЧА 1: Определи ТОП-ЦЕЛЬ ДНЯ
    Выбери одну цель из списка, которая должна быть приоритетной на сегодня. 
    Критерии выбора:
    - Максимальная важность и влияние на долгосрочные цели
    - Возможность выполнить за один день (2-6 часов работы)
    - Критичность для прогресса пользователя
    - Уникальность (не дублирует другие цели)
    
    ЗАДАЧА 2: Проанализируй каждую цель по SMART
    Для каждой цели оцени по критериям SMART (каждый критерий от 0 до 10):
    - S (Specific - Конкретность): Насколько четко и конкретно сформулирована цель?
    - M (Measurable - Измеримость): Можно ли измерить результат? Есть ли четкие критерии успеха?
    - A (Achievable - Достижимость): Реалистична ли цель? Можно ли ее достичь за указанное время?
    - R (Relevant - Релевантность): Насколько цель важна и актуальна? Соответствует ли она приоритетам?
    - T (Time-bound - Ограниченность во времени): Есть ли четкий дедлайн или временные рамки?
    
    ВАЖНО: Ответь СТРОГО в следующем JSON формате (без дополнительного текста до или после):
    {{
        "top_goal": {{
            "goal": "текст выбранной топ-цели",
            "reason": "краткое обоснование (2-3 предложения), почему именно эта цель"
        }},
        "smart_analysis": [
            {{
                "goal": "текст цели 1",
                "smart": {{
                    "specific": {{"score": 8, "comment": "комментарий"}},
                    "measurable": {{"score": 7, "comment": "комментарий"}},
                    "achievable": {{"score": 9, "comment": "комментарий"}},
                    "relevant": {{"score": 8, "comment": "комментарий"}},
                    "time_bound": {{"score": 6, "comment": "комментарий"}}
                }},
                "overall_score": 7.6,
                "recommendations": "конкретные рекомендации по улучшению цели (2-3 предложения)"
            }},
            {{
                "goal": "текст цели 2",
                "smart": {{
                    "specific": {{"score": 5, "comment": "комментарий"}},
                    "measurable": {{"score": 4, "comment": "комментарий"}},
                    "achievable": {{"score": 6, "comment": "комментарий"}},
                    "relevant": {{"score": 7, "comment": "комментарий"}},
                    "time_bound": {{"score": 5, "comment": "комментарий"}}
                }},
                "overall_score": 5.4,
                "recommendations": "рекомендации по улучшению"
            }}
        ]
        // ... для всех целей
    }}
    
    Комментарии должны быть краткими (1 предложение), конкретными и конструктивными.
    Пиши на русском языке.
    """
    
    try:
        chat_response = await client.chat.complete_async(
            model="mistral-medium",
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            response_format={
                "type": "json_object",
            }
        )
        
        response_text = chat_response.choices[0].message.content.strip()
        
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
        else:
            json_str = response_text
        
        try:
            result = json.loads(json_str)
            
            if 'top_goal' not in result:
                result['top_goal'] = {
                    'goal': goals_text_list[0] if goals_text_list else '',
                    'reason': 'Топ-цель не определена в ответе AI.'
                }
            if 'smart_analysis' not in result:
                result['smart_analysis'] = []
            
            return result
        except json.JSONDecodeError as e:
            print(f"Ошибка парсинга JSON от Mistral: {e}")
            print(f"Ответ: {response_text[:500]}...")
            return {
                'top_goal': {
                    'goal': goals_text_list[0] if goals_text_list else '',
                    'reason': (
                        'Ошибка при парсинге ответа AI. '
                        'Используется первая цель из списка.'
                    )
                },
                'smart_analysis': []
            }
            
    except Exception as e:
        print(f"Mistral analyze_goals_list error: {e}")
        return {
            'top_goal': {
                'goal': goals_text_list[0] if goals_text_list else '',
                'reason': f'Ошибка при анализе: {str(e)}'
            },
            'smart_analysis': []
        }

