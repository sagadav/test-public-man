from aiogram import types, F
from aiogram.fsm.context import FSMContext
from datetime import datetime, timedelta

from states import GoalStates
from keyboards import get_start_keyboard, get_replace_goal_keyboard
from db import (
    add_goal,
    update_goal_status,
    get_user_goal_for_date,
    delete_goal
)
from analysis import generate_clarifying_question, brainstorm_goal_failure
from services.ai_response_service import save_and_get_rating_keyboard


async def register_goals_handlers(dp, session_maker, bot):
    """Регистрация обработчиков для работы с целями"""

    @dp.message(F.text == "🎯 Топ-цель на завтра")
    async def start_goal_setting(
        message: types.Message,
        state: FSMContext
    ):
        await state.set_state(GoalStates.setting_goal)
        goal_description = (
            "<b>🎯 Что такое Топ-цель?</b>\n\n"
            "Это одна главная задача на завтра, "
            "которая продвинет тебя вперед. "
            "Чтобы она работала, она должна быть:\n"
            "1. <b>Конкретной</b> (что именно сделать?)\n"
            "2. <b>Измеримой</b> (как понять, что готово?)\n"
            "3. <b>Достижимой</b> (занимает 2-6 часов времени).\n\n"
            "Напиши свою Топ-цель на завтра:"
        )
        await message.answer(
            goal_description,
            parse_mode="HTML",
            reply_markup=types.ReplyKeyboardRemove()
        )

    @dp.message(GoalStates.setting_goal)
    async def process_goal(
        message: types.Message,
        state: FSMContext
    ):
        goal_text = message.text
        await state.update_data(goal_text=goal_text)
        await state.set_state(GoalStates.setting_result)

        await message.answer("Секунду...")
        question = await generate_clarifying_question(goal_text)

        # Сохраняем ответ AI и получаем клавиатуру оценки
        kb_rating = await save_and_get_rating_keyboard(
            session_maker,
            message.from_user.id,
            goal_text,
            question
        )

        await message.answer(
            question,
            parse_mode="HTML",
            reply_markup=kb_rating
        )

    @dp.message(GoalStates.setting_result)
    async def process_result(
        message: types.Message,
        state: FSMContext
    ):
        nonlocal session_maker
        data = await state.get_data()
        goal_text = data['goal_text']
        result_text = message.text
        user_id = message.from_user.id

        # Цель на завтра
        target_date = datetime.now() + timedelta(days=1)

        if session_maker:
            # Проверяем, есть ли уже цель на эту дату
            existing_goal = await get_user_goal_for_date(
                session_maker,
                user_id,
                target_date
            )

            if existing_goal:
                # Сохраняем данные новой цели в state для возможной замены
                await state.update_data(
                    new_goal_text=goal_text,
                    new_result_text=result_text,
                    existing_goal_id=existing_goal.id
                )
                await state.set_state(GoalStates.confirming_replace)

                await message.answer(
                    f"⚠️ <b>У тебя уже есть цель на завтра:</b>\n\n"
                    f"🎯 {existing_goal.goal_text}\n"
                    f"🏁 Результат: {existing_goal.result_text}\n\n"
                    f"<b>Новая цель:</b>\n"
                    f"🎯 {goal_text}\n"
                    f"🏁 Результат: {result_text}\n\n"
                    f"Заменить старую цель на новую?",
                    reply_markup=get_replace_goal_keyboard(),
                    parse_mode="HTML"
                )
            else:
                # Нет существующей цели, просто сохраняем
                await add_goal(
                    session_maker,
                    user_id,
                    goal_text,
                    result_text,
                    target_date
                )
                await message.answer(
                    f"✅ <b>Топ-цель сохранена!</b>\n\n"
                    f"🎯 <b>Задача:</b> {goal_text}\n"
                    f"🏁 <b>Результат:</b> {result_text}\n\n"
                    f"Я напомню тебе о ней.",
                    reply_markup=get_start_keyboard(),
                    parse_mode="HTML"
                )
                await state.clear()
        else:
            await message.answer(
                "Ошибка: База данных не подключена.",
                reply_markup=get_start_keyboard()
            )
            await state.clear()

    @dp.callback_query(
        F.data.startswith("replace_goal:"),
        GoalStates.confirming_replace
    )
    async def process_replace_goal(
        callback: types.CallbackQuery,
        state: FSMContext
    ):
        nonlocal session_maker
        action = callback.data.split(":")[1]
        data = await state.get_data()

        if action == "yes":
            # Заменяем цель
            existing_goal_id = data.get('existing_goal_id')
            new_goal_text = data.get('new_goal_text')
            new_result_text = data.get('new_result_text')
            user_id = callback.from_user.id
            target_date = datetime.now() + timedelta(days=1)

            if session_maker and existing_goal_id:
                # Удаляем старую цель
                await delete_goal(session_maker, existing_goal_id)
                # Добавляем новую цель
                await add_goal(
                    session_maker,
                    user_id,
                    new_goal_text,
                    new_result_text,
                    target_date
                )

                await callback.message.edit_text(
                    f"✅ <b>Топ-цель заменена!</b>\n\n"
                    f"🎯 <b>Задача:</b> {new_goal_text}\n"
                    f"🏁 <b>Результат:</b> {new_result_text}\n\n"
                    f"Я напомню тебе о ней.",
                    parse_mode="HTML"
                )
                await callback.message.answer(
                    "Выбери действие:",
                    reply_markup=get_start_keyboard()
                )
            else:
                await callback.message.edit_text(
                    "Ошибка при замене цели.",
                    parse_mode="HTML"
                )
        else:
            # Отмена замены
            await callback.message.edit_text(
                "❌ Замена отменена. Старая цель сохранена.",
                parse_mode="HTML"
            )
            await callback.message.answer(
                "Выбери действие:",
                reply_markup=get_start_keyboard()
            )

        await callback.answer()
        await state.clear()

    @dp.callback_query(F.data.startswith("goal_done:"))
    async def process_goal_done(callback: types.CallbackQuery):
        nonlocal session_maker
        goal_id = int(callback.data.split(":")[1])
        if session_maker:
            await update_goal_status(session_maker, goal_id, 1)
            await callback.message.edit_text(
                f"{callback.message.text}\n\n"
                f"✅ <b>Отлично! Цель выполнена. Так держать!</b>",
                parse_mode="HTML"
            )
        await callback.answer()

    @dp.callback_query(F.data.startswith("goal_fail:"))
    async def process_goal_fail(
        callback: types.CallbackQuery,
        state: FSMContext
    ):
        nonlocal session_maker
        # Извлекаем текст цели и результата из сообщения
        msg_lines = callback.message.text.split("\n")
        goal_text = ""
        result_text = ""
        for line in msg_lines:
            if line.startswith("🎯"):
                goal_text = line.replace("🎯", "").strip()
            if line.startswith("🏁"):
                result_text = line.replace("🏁 Результат:", "").strip()

        await state.update_data(
            fail_goal_text=goal_text,
            fail_result_text=result_text
        )
        await state.set_state(GoalStates.brainstorming_failure)

        fail_message = (
            "❌ <b>Цель не выполнена. Давай разберемся почему.</b>\n\n"
            "Ничего страшного, это опыт. Что именно сегодня помешало? "
            "Напиши кратко "
            "(например: 'устал', 'много мелких дел', "
            "'не знал с чего начать')."
        )
        await callback.message.edit_text(
            fail_message,
            parse_mode="HTML"
        )
        await callback.answer()

    @dp.message(GoalStates.brainstorming_failure)
    async def process_failure_reason(
        message: types.Message,
        state: FSMContext
    ):
        nonlocal session_maker
        reason = message.text
        data = await state.get_data()
        goal_text = data.get('fail_goal_text', 'Цель')
        result_text = data.get('fail_result_text', 'Результат')

        await message.answer("🤔 Анализирую ситуацию, одну секунду...")

        # Вызываем AI для совета
        advice = await brainstorm_goal_failure(
            goal_text,
            result_text,
            reason
        )

        # Формируем текст пользователя для сохранения
        user_text = (
            f"Цель: {goal_text}. "
            f"Результат: {result_text}. "
            f"Причина невыполнения: {reason}"
        )

        # Сохраняем ответ AI и получаем клавиатуру оценки
        kb_rating = await save_and_get_rating_keyboard(
            session_maker,
            message.from_user.id,
            user_text,
            advice
        )

        # Отправляем ответ с кнопками оценки (если есть)
        await message.answer(
            advice,
            parse_mode="markdown",
            reply_markup=kb_rating
        )

        # Отправляем главное меню отдельным сообщением
        await message.answer(
            "Выбери действие:",
            reply_markup=get_start_keyboard()
        )
        await state.clear()
