from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)


def get_start_keyboard() -> ReplyKeyboardMarkup:
    """Главная клавиатура"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔴 Записать срыв")],
            [KeyboardButton(text="🎯 Топ-цель на завтра")],
            [KeyboardButton(text="📜 История")],
            [KeyboardButton(text="⚙️ Настройки")]
        ],
        resize_keyboard=True
    )


def get_emotions_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура выбора эмоций"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="😰 Стресс"),
                KeyboardButton(text="😐 Скука")
            ],
            [
                KeyboardButton(text="😠 Злость"),
                KeyboardButton(text="😫 Усталость")
            ],
            [
                KeyboardButton(text="🥪 Голод"),
                KeyboardButton(text="🐺 Одиночество")
            ],
            [KeyboardButton(text="✏️ Другое")]
        ],
        resize_keyboard=True
    )


def get_location_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура выбора места"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🏠 Дом"),
                KeyboardButton(text="🏢 Работа")
            ],
            [
                KeyboardButton(text="🍷 Бар/Тусовка"),
                KeyboardButton(text="🚶 Улица")
            ],
            [KeyboardButton(text="✏️ Другое")]
        ],
        resize_keyboard=True
    )


def get_company_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура выбора компании"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="👤 Один"),
                KeyboardButton(text="💼 Коллеги")
            ],
            [
                KeyboardButton(text="👫 Друзья"),
                KeyboardButton(text="👪 Семья")
            ],
            [KeyboardButton(text="✏️ Другое")]
        ],
        resize_keyboard=True
    )


def get_rating_keyboard(response_id: int) -> InlineKeyboardMarkup:
    """Клавиатура оценки ответа AI"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="👍",
                    callback_data=f"rate_up:{response_id}"
                ),
                InlineKeyboardButton(
                    text="👎",
                    callback_data=f"rate_down:{response_id}"
                )
            ]
        ]
    )


def get_goal_check_keyboard(goal_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для проверки выполнения цели"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Сделано",
                    callback_data=f"goal_done:{goal_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Нет",
                    callback_data=f"goal_fail:{goal_id}"
                )
            ]
        ]
    )

