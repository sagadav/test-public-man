from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from keyboards import get_start_keyboard


class ErrorHandlerMiddleware(BaseMiddleware):
    """Middleware for centralized error handling"""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        try:
            return await handler(event, data)
        except (ValueError, IndexError) as e:
            print(f"Validation error: {e}")
            error_message = (
                "Ошибка при обработке данных. "
                "Пожалуйста, попробуйте еще раз."
            )
            await self._send_error_message(event, error_message)
        except Exception as e:
            print(f"Unexpected error: {e}")
            error_message = (
                "Произошла ошибка. Пожалуйста, попробуйте позже."
            )
            await self._send_error_message(event, error_message)

    async def _send_error_message(
        self, event: TelegramObject, message: str
    ):
        """Send error message to user"""
        if isinstance(event, Message):
            await event.answer(
                message,
                reply_markup=get_start_keyboard()
            )
        elif isinstance(event, CallbackQuery):
            await event.answer(
                message,
                show_alert=True
            )
            if event.message:
                try:
                    await event.message.answer(
                        message,
                        reply_markup=get_start_keyboard()
                    )
                except Exception:
                    pass
