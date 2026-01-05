import asyncio
from aiogram import Bot, Dispatcher

from config import TOKEN
from database import init_session_maker
from handlers import start, journal, goals, ratings, settings
from services.scheduler import scheduler_loop
from middleware import DatabaseCheckMiddleware, ErrorHandlerMiddleware


async def main():
    """Главная функция запуска бота"""
    # Инициализация бота и диспетчера
    bot = Bot(token=TOKEN)
    dp = Dispatcher()

    # Подключение к базе данных
    session_maker = None
    try:
        session_maker = await init_session_maker()
        print("База данных (ORM) подключена успешно.")
    except Exception as e:
        print(f"Ошибка подключения к БД: {e}")

    # Регистрация middleware для проверки подключения БД
    dp.message.middleware(DatabaseCheckMiddleware(session_maker))
    dp.callback_query.middleware(DatabaseCheckMiddleware(session_maker))

    # Регистрация middleware для обработки ошибок
    dp.message.middleware(ErrorHandlerMiddleware())
    dp.callback_query.middleware(ErrorHandlerMiddleware())

    # Регистрация всех обработчиков
    await start.register_start_handlers(dp, session_maker)
    await journal.register_journal_handlers(dp, session_maker)
    await goals.register_goals_handlers(dp, session_maker, bot)
    await ratings.register_ratings_handlers(dp, session_maker)
    await settings.register_settings_handlers(dp, session_maker)

    # Запускаем планировщик в фоне
    asyncio.create_task(scheduler_loop(bot, session_maker))

    # Запуск бота
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
