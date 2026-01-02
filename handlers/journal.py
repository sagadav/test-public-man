from aiogram import types, F
from aiogram.fsm.context import FSMContext

from states import TriggerJournal
from keyboards import (
    get_emotions_keyboard,
    get_location_keyboard,
    get_company_keyboard,
    get_start_keyboard
)
from db import add_entry


async def register_journal_handlers(dp, session_maker):
    """Регистрация обработчиков для журнала триггеров"""

    @dp.message(F.text == "🔴 Записать срыв")
    async def start_log(message: types.Message, state: FSMContext):
        await state.set_state(TriggerJournal.emotion)
        await message.answer(
            "Что ты чувствовал за 5 минут до этого?",
            reply_markup=get_emotions_keyboard()
        )

    async def ask_location(message: types.Message, state: FSMContext):
        await state.set_state(TriggerJournal.location)
        await message.answer(
            "Где ты находишься?",
            reply_markup=get_location_keyboard()
        )

    @dp.message(TriggerJournal.emotion)
    async def process_emotion(
        message: types.Message,
        state: FSMContext
    ):
        if message.text == "✏️ Другое":
            await state.set_state(TriggerJournal.emotion_custom)
            await message.answer(
                "Напиши, что ты чувствовал:",
                reply_markup=types.ReplyKeyboardRemove()
            )
        else:
            await state.update_data(emotion=message.text)
            await ask_location(message, state)

    @dp.message(TriggerJournal.emotion_custom)
    async def process_emotion_custom(
        message: types.Message,
        state: FSMContext
    ):
        await state.update_data(emotion=message.text)
        await ask_location(message, state)

    async def ask_company(message: types.Message, state: FSMContext):
        await state.set_state(TriggerJournal.company)
        await message.answer(
            "Кто рядом с тобой?",
            reply_markup=get_company_keyboard()
        )

    @dp.message(TriggerJournal.location)
    async def process_location(
        message: types.Message,
        state: FSMContext
    ):
        if message.text == "✏️ Другое":
            await state.set_state(TriggerJournal.location_custom)
            await message.answer(
                "Где именно?",
                reply_markup=types.ReplyKeyboardRemove()
            )
        else:
            await state.update_data(location=message.text)
            await ask_company(message, state)

    @dp.message(TriggerJournal.location_custom)
    async def process_location_custom(
        message: types.Message,
        state: FSMContext
    ):
        await state.update_data(location=message.text)
        await ask_company(message, state)

    async def finish_log(
        message: types.Message,
        state: FSMContext,
        company_text: str
    ):
        nonlocal session_maker
        data = await state.get_data()
        emotion = data['emotion']
        location = data['location']

        if session_maker:
            await add_entry(
                session_maker,
                message.from_user.id,
                emotion,
                location,
                company_text
            )
        else:
            await message.answer("Ошибка: База данных не подключена.")

        response_text = (
            f"Записано: {emotion} + {location} + {company_text}.\n\n"
        )

        await message.answer(
            response_text,
            reply_markup=get_start_keyboard(),
            parse_mode="HTML"
        )
        await state.clear()

        # Проверка на необходимость анализа
        if session_maker:
            from services.analysis_service import process_analysis_with_rating

            # Формируем текст пользователя для сохранения
            user_text = (
                f"Запись триггера: {emotion} + {location} + {company_text}"
            )

            await process_analysis_with_rating(
                session_maker,
                message.from_user.id,
                message,
                user_text
            )

    @dp.message(TriggerJournal.company)
    async def process_company(
        message: types.Message,
        state: FSMContext
    ):
        if message.text == "✏️ Другое":
            await state.set_state(TriggerJournal.company_custom)
            await message.answer(
                "С кем именно?",
                reply_markup=types.ReplyKeyboardRemove()
            )
        else:
            await finish_log(message, state, message.text)

    @dp.message(TriggerJournal.company_custom)
    async def process_company_custom(
        message: types.Message,
        state: FSMContext
    ):
        await finish_log(message, state, message.text)

