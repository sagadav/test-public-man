from aiogram import types, F
from aiogram.fsm.context import FSMContext

from states import TriggerJournal
from keyboards import (
    get_emotions_keyboard,
    get_location_keyboard,
    get_company_keyboard,
    get_start_keyboard
)
from repositories import JournalRepository


async def register_journal_handlers(dp, session_maker):
    """Регистрация обработчиков для журнала триггеров"""

    @dp.message(F.text == "🔴 Записать срыв")
    async def start_log(message: types.Message, state: FSMContext):
        await state.clear()
        await state.set_state(TriggerJournal.emotion)
        await message.answer(
            "Что ты чувствовал за 5 минут до этого?",
            reply_markup=get_emotions_keyboard()
        )

    async def ask_location(callback_or_message, state: FSMContext):
        """Вспомогательная функция для запроса места"""
        await state.set_state(TriggerJournal.location)
        text = "Где ты находишься?"
        if isinstance(callback_or_message, types.CallbackQuery):
            await callback_or_message.message.edit_text(
                text,
                reply_markup=get_location_keyboard()
            )
        else:
            await callback_or_message.answer(
                text,
                reply_markup=get_location_keyboard()
            )

    @dp.callback_query(F.data.startswith("emotion:"), TriggerJournal.emotion)
    async def process_emotion(
        callback: types.CallbackQuery,
        state: FSMContext
    ):
        emotion_value = callback.data.split(":", 1)[1]

        if emotion_value == "custom":
            await state.set_state(TriggerJournal.emotion_custom)
            await callback.message.edit_text(
                "Напиши, что ты чувствовал:"
            )
        else:
            await state.update_data(emotion=emotion_value)
            await ask_location(callback, state)
        await callback.answer()

    @dp.message(TriggerJournal.emotion_custom)
    async def process_emotion_custom(
        message: types.Message,
        state: FSMContext
    ):
        await state.update_data(emotion=message.text)
        await ask_location(message, state)

    async def ask_company(callback_or_message, state: FSMContext):
        """Вспомогательная функция для запроса компании"""
        await state.set_state(TriggerJournal.company)
        text = "Кто рядом с тобой?"
        if isinstance(callback_or_message, types.CallbackQuery):
            await callback_or_message.message.edit_text(
                text,
                reply_markup=get_company_keyboard()
            )
        else:
            await callback_or_message.answer(
                text,
                reply_markup=get_company_keyboard()
            )

    @dp.callback_query(F.data.startswith("location:"), TriggerJournal.location)
    async def process_location(
        callback: types.CallbackQuery,
        state: FSMContext
    ):
        location_value = callback.data.split(":", 1)[1]

        if location_value == "custom":
            await state.set_state(TriggerJournal.location_custom)
            await callback.message.edit_text("Где именно?")
        else:
            await state.update_data(location=location_value)
            await ask_company(callback, state)
        await callback.answer()

    @dp.message(TriggerJournal.location_custom)
    async def process_location_custom(
        message: types.Message,
        state: FSMContext
    ):
        await state.update_data(location=message.text)
        await ask_company(message, state)

    async def finish_log(
        callback_or_message,
        state: FSMContext,
        company_text: str
    ):
        """Завершение записи срыва"""
        nonlocal session_maker
        data = await state.get_data()
        emotion = data['emotion']
        location = data['location']

        # Получаем user_id в зависимости от типа объекта
        if isinstance(callback_or_message, types.CallbackQuery):
            user_id = callback_or_message.from_user.id
            message_obj = callback_or_message.message
        else:
            user_id = callback_or_message.from_user.id
            message_obj = callback_or_message

        journal_repo = JournalRepository(session_maker)
        await journal_repo.add_entry(
            user_id,
            emotion,
            location,
            company_text
        )

        response_text = (
            f"Записано: {emotion} + {location} + {company_text}.\n\n"
        )

        if isinstance(callback_or_message, types.CallbackQuery):
            await callback_or_message.message.edit_text(
                response_text,
                parse_mode="HTML"
            )
            await callback_or_message.message.answer(
                "Выбери действие:",
                reply_markup=get_start_keyboard()
            )
        else:
            await callback_or_message.answer(
                response_text,
                reply_markup=get_start_keyboard(),
                parse_mode="HTML"
            )
        await state.clear()

        from services.analysis_service import process_analysis_with_rating

        user_text = (
            f"Запись триггера: {emotion} + {location} + {company_text}"
        )

        await process_analysis_with_rating(
            session_maker,
            user_id,
            message_obj,
            user_text
        )

    @dp.callback_query(F.data.startswith("company:"), TriggerJournal.company)
    async def process_company(
        callback: types.CallbackQuery,
        state: FSMContext
    ):
        company_value = callback.data.split(":", 1)[1]

        if company_value == "custom":
            await state.set_state(TriggerJournal.company_custom)
            await callback.message.edit_text("С кем именно?")
        else:
            await finish_log(callback, state, company_value)
        await callback.answer()

    @dp.message(TriggerJournal.company_custom)
    async def process_company_custom(
        message: types.Message,
        state: FSMContext
    ):
        await finish_log(message, state, message.text)
