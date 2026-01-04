from aiogram import types, F
from aiogram.fsm.context import FSMContext
from datetime import datetime, timedelta

from states import GoalStates
from keyboards import (
    get_start_keyboard,
    get_replace_goal_keyboard,
    get_new_goal_keyboard
)
from repositories import GoalRepository
from analysis import (
    generate_clarifying_question,
    brainstorm_goal_failure,
    analyze_goals_list
)
from services.ai_response_service import save_and_get_rating_keyboard

# Максимальная длина сообщения в Telegram (с запасом для безопасности)
MAX_MESSAGE_LENGTH = 4000


def split_long_message(
    text: str, max_length: int = MAX_MESSAGE_LENGTH
) -> list[str]:
    """
    Разбивает длинный текст на части, не превышающие max_length символов.
    Старается разбивать по переносам строк, чтобы не разрывать структуру.
    
    Args:
        text: Текст для разбиения
        max_length: Максимальная длина одной части
        
    Returns:
        Список частей текста
    """
    if len(text) <= max_length:
        return [text]
    
    parts = []
    current_part = ""
    
    # Разбиваем по переносам строк
    lines = text.split('\n')
    
    for line in lines:
        # Если текущая часть + новая строка помещается
        if len(current_part) + len(line) + 1 <= max_length:
            if current_part:
                current_part += '\n' + line
            else:
                current_part = line
        else:
            # Сохраняем текущую часть и начинаем новую
            if current_part:
                parts.append(current_part)
            
            # Если одна строка слишком длинная, разбиваем её
            if len(line) > max_length:
                # Разбиваем длинную строку по словам
                words = line.split(' ')
                current_part = ""
                for word in words:
                    if len(current_part) + len(word) + 1 <= max_length:
                        if current_part:
                            current_part += ' ' + word
                        else:
                            current_part = word
                    else:
                        if current_part:
                            parts.append(current_part)
                        current_part = word
            else:
                current_part = line
    
    # Добавляем последнюю часть
    if current_part:
        parts.append(current_part)
    
    return parts


async def register_goals_handlers(dp, session_maker, bot):
    """Регистрация обработчиков для работы с целями"""

    @dp.message(F.text == "🎯 Топ-цель на завтра")
    async def start_goal_setting(
        message: types.Message,
        state: FSMContext
    ):
        await state.clear()
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

        target_date = datetime.now() + timedelta(days=1)

        goal_repo = GoalRepository(session_maker)
        existing_goal = await goal_repo.get_user_goal_for_date(
            user_id,
            target_date
        )

        if existing_goal:
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
            await goal_repo.add_goal(
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

            if not existing_goal_id:
                await callback.message.edit_text(
                    "Ошибка при замене цели.",
                    parse_mode="HTML"
                )
                await callback.answer()
                await state.clear()
                return

            goal_repo = GoalRepository(session_maker)
            await goal_repo.delete_goal(existing_goal_id)
            await goal_repo.add_goal(
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

        goal_repo = GoalRepository(session_maker)
        await goal_repo.update_goal_status(goal_id, 1)
        await callback.message.edit_text(
            f"{callback.message.text}\n\n"
            f"✅ <b>Отлично! Цель выполнена. Так держать!</b>",
            parse_mode="HTML",
            reply_markup=get_new_goal_keyboard()
        )
        await callback.answer()

    @dp.callback_query(F.data == "new_goal_tomorrow")
    async def start_new_goal_from_callback(
        callback: types.CallbackQuery,
        state: FSMContext
    ):
        """Обработчик для создания новой цели через inline кнопку"""
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
        await callback.message.answer(
            goal_description,
            parse_mode="HTML",
            reply_markup=types.ReplyKeyboardRemove()
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
            "Не сдавайтесь! Добавьте новую цель на завтра.",
            reply_markup=get_start_keyboard()
        )
        await state.clear()

    @dp.message(F.text == "📊 Анализ ваших целей")
    async def start_goals_analysis(
        message: types.Message,
        state: FSMContext
    ):
        """Начало процесса анализа целей - запрос списка"""
        await state.clear()
        await state.set_state(GoalStates.analyzing_goals)
        await message.answer(
            "<b>📊 Анализ ваших целей</b>\n\n"
            "Отправьте список ваших целей для анализа.\n\n"
            "Можно отправить цели в любом формате:\n"
            "• Каждая цель с новой строки\n"
            "• С номерами или без\n\n"
            "<i>Пример:</i>\n"
            "1. Написать отчет по проекту\n"
            "2. Подготовить презентацию\n"
            "3. Провести встречу с командой",
            parse_mode="HTML",
            reply_markup=types.ReplyKeyboardRemove()
        )

    @dp.message(GoalStates.analyzing_goals)
    async def process_goals_analysis(
        message: types.Message,
        state: FSMContext
    ):
        """Обработка списка целей и их анализ"""
        nonlocal session_maker
        user_id = message.from_user.id

        # Парсим список целей из текста
        goals_text = message.text.strip()
        
        # Разбиваем на отдельные цели
        # Пробуем разные разделители: перенос строки, запятая, точка с запятой
        if '\n' in goals_text:
            goals_list = [g.strip() for g in goals_text.split('\n') if g.strip()]
        elif ';' in goals_text:
            goals_list = [g.strip() for g in goals_text.split(';') if g.strip()]
        elif ',' in goals_text:
            goals_list = [g.strip() for g in goals_text.split(',') if g.strip()]
        else:
            # Если одна цель
            goals_list = [goals_text]

        # Убираем номера и маркеры в начале строк
        cleaned_goals = []
        for goal in goals_list:
            # Убираем номера (1., 2., и т.д.)
            goal = goal.lstrip('0123456789. ')
            # Убираем маркеры (-, •, *, и т.д.)
            goal = goal.lstrip('- •*→ ')
            if goal:
                cleaned_goals.append(goal)

        if not cleaned_goals:
            await message.answer(
                "❌ Не удалось распознать цели в вашем сообщении.\n\n"
                "Пожалуйста, отправьте список целей еще раз, "
                "каждая цель с новой строки или через запятую.",
                parse_mode="HTML"
            )
            return

        await message.answer(
            f"🔍 Анализирую цели ({len(cleaned_goals)})... "
            "Это может занять несколько секунд."
        )

        # Анализируем цели
        analysis_result = await analyze_goals_list(cleaned_goals)

        # Форматируем результат
        response_text = "<b>📊 Анализ ваших целей</b>\n\n"

        # Топ-цель дня
        if analysis_result.get('top_goal'):
            top_goal = analysis_result['top_goal']
            response_text += (
                f"<b>🎯 Топ-цель дня:</b>\n"
                f"{top_goal.get('goal', 'Не определена')}\n\n"
                f"<i>{top_goal.get('reason', '')}</i>\n\n"
            )

        # SMART анализ каждой цели
        smart_analysis = analysis_result.get('smart_analysis', [])
        if smart_analysis:
            response_text += "<b>📋 SMART-анализ целей:</b>\n\n"
            
            for idx, goal_analysis in enumerate(smart_analysis, 1):
                goal_text = goal_analysis.get('goal', 'Цель')
                smart = goal_analysis.get('smart', {})
                overall_score = goal_analysis.get('overall_score', 0)
                recommendations = goal_analysis.get('recommendations', '')

                response_text += f"<b>{idx}. {goal_text}</b>\n"
                response_text += f"📊 Общий балл SMART: <b>{overall_score:.1f}/10</b>\n\n"

                # Детали по каждому критерию SMART
                smart_criteria = {
                    'specific': 'S (Конкретность)',
                    'measurable': 'M (Измеримость)',
                    'achievable': 'A (Достижимость)',
                    'relevant': 'R (Релевантность)',
                    'time_bound': 'T (Ограниченность во времени)'
                }

                for key, label in smart_criteria.items():
                    criterion = smart.get(key, {})
                    score = criterion.get('score', 0)
                    comment = criterion.get('comment', '')
                    response_text += f"  {label}: {score}/10\n"
                    if comment:
                        response_text += f"    <i>{comment}</i>\n"

                if recommendations:
                    response_text += f"\n💡 <b>Рекомендации:</b> {recommendations}\n"

                response_text += "\n" + "─" * 30 + "\n\n"

        # Сохраняем ответ AI для оценки
        user_text = f"Анализ {len(cleaned_goals)} целей: {', '.join(cleaned_goals[:3])}"
        ai_response_text = response_text
        kb_rating = await save_and_get_rating_keyboard(
            session_maker,
            user_id,
            user_text,
            ai_response_text
        )

        # Разбиваем длинное сообщение на части
        message_parts = split_long_message(response_text)
        
        # Отправляем все части, кроме последней
        for part in message_parts[:-1]:
            await message.answer(
                part,
                parse_mode="HTML"
            )
        
        # Последнюю часть отправляем с клавиатурой оценки
        if message_parts:
            await message.answer(
                message_parts[-1],
                parse_mode="HTML",
                reply_markup=kb_rating
            )

        # Возвращаем главное меню
        await message.answer(
            "Выбери действие:",
            reply_markup=get_start_keyboard()
        )
        await state.clear()
