from repositories import AIRepository
from keyboards import get_rating_keyboard


async def save_ai_response(
    session_maker,
    user_id: int,
    user_text: str,
    ai_response: str
) -> int | None:
    """
    Сохраняет ответ AI в базу данных.
    Возвращает ID сохраненной записи или None в случае ошибки.
    """
    try:
        ai_repo = AIRepository(session_maker)
        response_id = await ai_repo.add_ai_response(
            user_id,
            user_text,
            ai_response
        )
        return response_id
    except Exception as e:
        print(f"Ошибка при сохранении ответа AI: {e}")
        return None


async def save_and_get_rating_keyboard(
    session_maker,
    user_id: int,
    user_text: str,
    ai_response: str
):
    """
    Сохраняет ответ AI и возвращает клавиатуру для оценки.
    
    Returns:
        InlineKeyboardMarkup | None: Клавиатура с кнопками оценки
            или None, если сохранение не удалось
    """
    response_id = await save_ai_response(
        session_maker,
        user_id,
        user_text,
        ai_response
    )

    if response_id is not None:
        return get_rating_keyboard(response_id)
    return None

