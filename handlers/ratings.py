from aiogram import types, F

from repositories import AIRepository


async def register_ratings_handlers(dp, session_maker):
    """Регистрация обработчиков для оценки ответов AI"""

    @dp.callback_query(F.data.startswith("rate_up:"))
    async def process_rate_up(callback: types.CallbackQuery):
        nonlocal session_maker
        try:
            response_id = int(callback.data.split(":")[1])

            ai_repo = AIRepository(session_maker)
            await ai_repo.update_ai_rating(response_id, 1)
            await callback.answer(
                "Спасибо за оценку! 👍",
                show_alert=False
            )
        except (ValueError, IndexError) as e:
            print(f"Ошибка при обработке оценки: {e}")
            await callback.answer(
                "Ошибка при сохранении оценки.",
                show_alert=True
            )

    @dp.callback_query(F.data.startswith("rate_down:"))
    async def process_rate_down(callback: types.CallbackQuery):
        nonlocal session_maker
        try:
            response_id = int(callback.data.split(":")[1])

            ai_repo = AIRepository(session_maker)
            await ai_repo.update_ai_rating(response_id, -1)
            await callback.answer(
                "Спасибо за оценку! 👎",
                show_alert=False
            )
        except (ValueError, IndexError) as e:
            print(f"Ошибка при обработке оценки: {e}")
            await callback.answer(
                "Ошибка при сохранении оценки.",
                show_alert=True
            )

