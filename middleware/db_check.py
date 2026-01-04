from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from keyboards import get_start_keyboard


class DatabaseCheckMiddleware(BaseMiddleware):
    """Middleware для проверки подключения базы данных"""

    def __init__(self, session_maker):
        self.session_maker = session_maker

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        if not self.session_maker:
            if isinstance(event, Message):
                if event.text and event.text.startswith("/"):
                    return await handler(event, data)

                await event.answer(
                    "Ошибка: База данных не подключена.",
                    reply_markup=get_start_keyboard()
                )
                return

            elif isinstance(event, CallbackQuery):
                await event.message.answer(
                    "Ошибка: База данных не подключена.",
                    reply_markup=get_start_keyboard()
                )
                await event.answer()
                return

        return await handler(event, data)
