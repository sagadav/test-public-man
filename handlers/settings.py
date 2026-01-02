from aiogram import types, F
from aiogram.fsm.context import FSMContext
from datetime import datetime
import pytz

from states import SettingsStates
from db import set_user_timezone, get_user_settings
from services.timezone_service import detect_timezone_from_time


# Популярные часовые пояса
POPULAR_TIMEZONES = [
    ("Europe/Moscow", "🇷🇺 Москва (UTC+3)"),
    ("Europe/Minsk", "🇧🇾 Минск (UTC+3)"),
    ("Asia/Almaty", "🇰🇿 Алматы (UTC+6)"),
    ("Asia/Tashkent", "🇺🇿 Ташкент (UTC+5)"),
    ("Europe/London", "🇬🇧 Лондон (UTC+0)"),
    ("America/New_York", "🇺🇸 Нью-Йорк (UTC-5)"),
    ("America/Los_Angeles", "🇺🇸 Лос-Анджелес (UTC-8)"),
    ("Asia/Tokyo", "🇯🇵 Токио (UTC+9)"),
    ("Asia/Shanghai", "🇨🇳 Шанхай (UTC+8)"),
]


async def register_settings_handlers(dp, session_maker):
    """Регистрация обработчиков для настроек"""

    @dp.message(F.text == "⚙️ Настройки")
    async def show_settings(message: types.Message):
        nonlocal session_maker
        user_settings = await get_user_settings(
            session_maker,
            message.from_user.id
        )

        current_tz = user_settings.timezone if user_settings else None
        tz_info = ""
        if current_tz:
            try:
                tz = pytz.timezone(current_tz)
                now = datetime.now(tz)
                offset = now.strftime("%z")
                tz_info = (
                    f"\n\nТекущий часовой пояс: {current_tz} ({offset})"
                )
            except Exception:
                tz_info = f"\n\nТекущий часовой пояс: {current_tz}"

        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        
        # Создаем клавиатуру с опциями
        settings_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📍 Выбрать из списка",
                    callback_data="tz_show_list"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🕐 Определить по времени",
                    callback_data="tz_detect_by_time"
                )
            ]
        ])
        
        await message.answer(
            f"⚙️ <b>Настройки</b>{tz_info}\n\n"
            "Выбери способ установки часового пояса:",
            parse_mode="HTML",
            reply_markup=settings_keyboard
        )

    @dp.callback_query(F.data == "tz_show_list")
    async def show_timezone_list(callback: types.CallbackQuery):
        await callback.message.edit_text(
            "📍 <b>Выбери часовой пояс:</b>",
            parse_mode="HTML",
            reply_markup=get_timezone_keyboard()
        )
        await callback.answer()

    @dp.callback_query(F.data == "tz_detect_by_time")
    async def start_timezone_detection(
        callback: types.CallbackQuery,
        state: FSMContext
    ):
        await state.set_state(SettingsStates.setting_timezone_by_time)
        await callback.message.edit_text(
            "🕐 <b>Определение часового пояса по времени</b>\n\n"
            "Отправь мне текущее время в формате <b>HH:MM</b>\n"
            "Например: <code>14:30</code> или <code>9:15</code>\n\n"
            "Я сравню твоё время с серверным и определю твой часовой пояс.",
            parse_mode="HTML"
        )
        await callback.answer()

    @dp.message(SettingsStates.setting_timezone_by_time)
    async def process_user_time(message: types.Message, state: FSMContext):
        nonlocal session_maker
        user_time_str = message.text.strip()

        # Определяем часовой пояс
        timezone, error_msg = detect_timezone_from_time(
            user_time_str,
            POPULAR_TIMEZONES
        )
        
        if timezone:
            # Сохраняем часовой пояс
            try:
                await set_user_timezone(
                    session_maker,
                    message.from_user.id,
                    timezone
                )
                
                # Получаем информацию о часовом поясе
                tz = pytz.timezone(timezone)
                tz_now = datetime.now(tz)
                offset = tz_now.strftime("%z")
                offset_formatted = f"{offset[:3]}:{offset[3:]}"
                
                await message.answer(
                    f"✅ <b>Часовой пояс определен и установлен!</b>\n\n"
                    f"📍 Часовой пояс: <b>{timezone}</b>\n"
                    f"⏰ Смещение: <b>UTC{offset_formatted}</b>\n\n"
                    f"Напоминания будут приходить в 9:00 и 21:00 "
                    f"по твоему местному времени.",
                    parse_mode="HTML"
                )
            except Exception as e:
                print(f"Ошибка при сохранении часового пояса: {e}")
                await message.answer(
                    "❌ Ошибка при сохранении часового пояса. "
                    "Попробуй еще раз или выбери часовой пояс вручную."
                )
        else:
            await message.answer(
                f"❌ {error_msg}\n\n"
                "Попробуй еще раз или выбери часовой пояс из списка.",
                parse_mode="HTML"
            )
        
        await state.clear()

    @dp.callback_query(F.data.startswith("set_tz:"))
    async def set_timezone_callback(callback: types.CallbackQuery):
        nonlocal session_maker
        timezone = callback.data.split(":")[1]

        try:
            # Проверяем валидность часового пояса
            pytz.timezone(timezone)
            await set_user_timezone(
                session_maker,
                callback.from_user.id,
                timezone
            )
            tz_message = f"Часовой пояс установлен: {timezone}"
            await callback.answer(
                tz_message,
                show_alert=True
            )
            await callback.message.edit_text(
                f"✅ <b>Часовой пояс установлен!</b>\n\n"
                f"Часовой пояс: {timezone}\n\n"
                f"Напоминания будут приходить в 9:00 и 21:00 "
                f"по твоему местному времени.",
                parse_mode="HTML"
            )
        except pytz.exceptions.UnknownTimeZoneError:
            await callback.answer(
                "Ошибка: Неизвестный часовой пояс",
                show_alert=True
            )
        except Exception as e:
            print(f"Ошибка при установке часового пояса: {e}")
            await callback.answer(
                "Ошибка при сохранении настроек",
                show_alert=True
            )


def get_timezone_keyboard():
    """Создает клавиатуру для выбора часового пояса"""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    buttons = []
    for tz_name, tz_label in POPULAR_TIMEZONES:
        buttons.append([
            InlineKeyboardButton(
                text=tz_label,
                callback_data=f"set_tz:{tz_name}"
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)
