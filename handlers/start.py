from aiogram import types, F
from aiogram.filters import Command

from keyboards import get_start_keyboard
from db import get_entries


async def register_start_handlers(dp, session_maker):
    """Регистрация обработчиков для команды /start и истории"""
    
    @dp.message(Command("start"))
    async def cmd_start(message: types.Message):
        await message.answer(
            "Привет! У этого бота 2 функции:\n"
            "1. Я помогу тебе исследовать триггеры твоих привычек, "
            "используя принципы когнитивно-поведенческой терапии (КПТ).\n\n"
            "2. Я помогу тебе ставить и достигать Топ-целей на день. ",
            # "Помни: срыв — это не провал, а важный опыт для анализа. "
            # "Давай без осуждения разберемся, что произошло, "
            # "чтобы в будущем тебе было легче справляться. "
            # "Нажми на кнопку ниже, когда будешь готов сделать запись.",
            reply_markup=get_start_keyboard()
        )

    @dp.message(F.text == "📜 История")
    async def show_history(message: types.Message):
        nonlocal session_maker
        if not session_maker:
            await message.answer("Ошибка: База данных не подключена.")
            return

        entries = await get_entries(session_maker, message.from_user.id)

        if not entries:
            await message.answer("У тебя пока нет записей.")
            return

        text_response = "<b>📋 Твои последние записи:</b>\n\n"
        for entry in entries:
            date_str = entry.created_at.strftime("%d.%m %H:%M")
            text_response += f"🗓 <code>{date_str}</code>\n"
            text_response += (
                f"😰 {entry.emotion} | "
                f"📍 {entry.location} | "
                f"👥 {entry.company}\n\n"
            )

        await message.answer(text_response, parse_mode="HTML")

