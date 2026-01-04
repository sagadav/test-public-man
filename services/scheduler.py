import asyncio
from datetime import datetime
from aiogram import Bot

from repositories import GoalRepository, UserRepository
from keyboards import get_goal_check_keyboard
from services.timezone_service import is_time_for_reminder


async def send_morning_reminder(
    bot: Bot,
    session_maker,
    goal
):
    """Отправляет утреннее напоминание о цели"""
    try:
        await bot.send_message(
            goal.user_id,
            f"☀️ <b>Доброе утро! Твоя топ-цель на сегодня:</b>\n\n"
            f"🎯 {goal.goal_text}\n"
            f"🏁 Результат: {goal.result_text}\n\n"
            f"Удачи! Ты справишься.",
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"Ошибка отправки напоминания пользователю {goal.user_id}: {e}")


async def send_evening_check(
    bot: Bot,
    session_maker,
    goal
):
    """Отправляет вечерний чек-ин о выполнении цели"""
    try:
        kb_done = get_goal_check_keyboard(goal.id)
        await bot.send_message(
            goal.user_id,
            f"🌙 <b>Вечерний чек-ин. Как успехи с топ-целью?</b>\n\n"
            f"🎯 {goal.goal_text}\n"
            f"🏁 Результат: {goal.result_text}",
            reply_markup=kb_done,
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"Ошибка отправки опроса пользователю {goal.user_id}: {e}")


async def scheduler_loop(bot: Bot, session_maker):
    """
    Основной цикл планировщика напоминаний.
    Проверяет время для каждого пользователя в его часовом поясе
    и отправляет напоминания в 9:00 и 21:00 по местному времени.
    """
    # Словарь для отслеживания отправленных напоминаний
    # Ключ: (user_id, reminder_type), значение: дата последней отправки
    sent_reminders = {}

    while True:
        if not session_maker:
            await asyncio.sleep(60)
            continue

        # Получаем всех пользователей, у которых есть цели
        # Для пользователей без часового пояса будет использоваться UTC+5
        user_repo = UserRepository(session_maker)
        users_with_goals = await user_repo.get_all_users_with_goals()

        for user_settings in users_with_goals:
            user_id = user_settings.user_id
            from services.timezone_service import get_user_local_time
            user_time = get_user_local_time(user_settings)

            # Используем дату пользователя для проверки
            user_date = user_time.date()

            # Проверяем утреннее напоминание (09:00)
            if is_time_for_reminder(user_settings, 9):
                reminder_key = (user_id, 'morning')
                if sent_reminders.get(reminder_key) != user_date:
                    # Получаем активные цели пользователя на сегодня
                    goal_repo = GoalRepository(session_maker)
                    goals = await goal_repo.get_active_goals_for_date(user_time)
                    for goal in goals:
                        if goal.user_id == user_id:
                            await send_morning_reminder(
                                bot,
                                session_maker,
                                goal
                            )
                    sent_reminders[reminder_key] = user_date

            # Проверяем вечерний чек-ин (21:00)
            if is_time_for_reminder(user_settings, 21):
                reminder_key = (user_id, 'evening')
                if sent_reminders.get(reminder_key) != user_date:
                    goal_repo = GoalRepository(session_maker)
                    goals = await goal_repo.get_active_goals_for_date(user_time)
                    for goal in goals:
                        if goal.user_id == user_id:
                            await send_evening_check(
                                bot,
                                session_maker,
                                goal
                            )
                    sent_reminders[reminder_key] = user_date

        # Очищаем старые записи (старше 1 дня)
        current_date = datetime.now().date()
        sent_reminders = {
            k: v for k, v in sent_reminders.items()
            if v == current_date
        }

        # Ждем 60 секунд до следующей проверки
        await asyncio.sleep(60)
