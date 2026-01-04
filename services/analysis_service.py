from datetime import datetime, timedelta
from repositories import AnalysisRepository, JournalRepository
from analysis import analyze_with_mistral


async def should_analyze_entries(session_maker, user_id: int) -> bool:
    """
    Проверяет, нужно ли запускать анализ записей пользователя.
    
    Анализ запускается если:
    - Нет предыдущих анализов И есть >= 3 записей за неделю
    - Последний анализ был > 3 дней назад И есть >= 3 новых записей
    """
    analysis_repo = AnalysisRepository(session_maker)
    last_analysis = await analysis_repo.get_latest_analysis(user_id)

    if not last_analysis:
        # Если анализов нет, проверяем количество записей
        journal_repo = JournalRepository(session_maker)
        entries_week = await journal_repo.get_entries_since(
            user_id,
            datetime.now() - timedelta(days=7)
        )
        return len(entries_week) >= 3

    # Если анализ был, проверяем прошло ли 3 дня
    # if datetime.now() - last_analysis.created_at > timedelta(days=3):
    #     # И есть ли новые записи
    #     entries_since_last = await get_entries_since(
    #         session_maker,
    #         user_id,
    #         last_analysis.created_at
    #     )
    #     return len(entries_since_last) >= 3

    return True


async def analyze_user_entries(session_maker, user_id: int) -> str:
    """
    Анализирует записи пользователя за последнюю неделю.
    Возвращает результат анализа.
    """
    journal_repo = JournalRepository(session_maker)
    recent_entries = await journal_repo.get_entries_since(
        user_id,
        datetime.now() - timedelta(days=7)
    )

    entries_text = "\n".join([
        f"- {e.created_at.strftime('%d.%m %H:%M')}: "
        f"Эмоция '{e.emotion}', "
        f"Место '{e.location}', "
        f"С кем '{e.company}'"
        for e in recent_entries
    ])

    return await analyze_with_mistral(entries_text)


async def process_analysis_if_needed(
    session_maker,
    user_id: int,
    send_message_func
):
    """
    Проверяет и запускает анализ записей, если необходимо.
    Отправляет результаты пользователю.
    """
    if not session_maker:
        return

    try:
        if await should_analyze_entries(session_maker, user_id):
            await send_message_func(
                "🤖 Собираю данные для анализа твоих паттернов... "
                "Это займет пару секунд."
            )

            analysis_result = await analyze_user_entries(
                session_maker,
                user_id
            )

            # Сохраняем и отправляем
            analysis_repo = AnalysisRepository(session_maker)
            await analysis_repo.add_analysis(user_id, analysis_result)
            await send_message_func(
                analysis_result,
                parse_mode="Markdown"
            )
    except Exception as e:
        print(f"Ошибка при запуске анализа: {e}")


async def process_analysis_with_rating(
    session_maker,
    user_id: int,
    message,
    user_text: str = None
):
    """
    Проверяет и запускает анализ записей, если необходимо.
    Сохраняет ответ AI и отправляет с кнопками оценки.
    
    Args:
        session_maker: Фабрика сессий БД
        user_id: ID пользователя
        message: Объект сообщения для отправки ответа
        user_text: Текст пользователя для сохранения (опционально)
    """
    if not session_maker:
        return

    try:
        if await should_analyze_entries(session_maker, user_id):
            await message.answer(
                "🤖 Собираю данные для анализа твоих паттернов... "
                "Это займет пару секунд."
            )

            analysis_result = await analyze_user_entries(
                session_maker,
                user_id
            )

            # Сохраняем в таблицу анализов
            analysis_repo = AnalysisRepository(session_maker)
            await analysis_repo.add_analysis(user_id, analysis_result)

            # Формируем текст пользователя, если не передан
            if user_text is None:
                user_text = "Анализ записей журнала триггеров"

            # Сохраняем ответ AI и получаем клавиатуру оценки
            from services.ai_response_service import (
                save_and_get_rating_keyboard
            )
            kb_rating = await save_and_get_rating_keyboard(
                session_maker,
                user_id,
                user_text,
                analysis_result
            )

            # Отправляем результат с кнопками оценки
            await message.answer(
                analysis_result,
                parse_mode="Markdown",
                reply_markup=kb_rating
            )
    except Exception as e:
        print(f"Ошибка при запуске анализа: {e}")

