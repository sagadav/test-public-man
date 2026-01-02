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


def get_emotions_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора эмоций"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="😰 Стресс",
                    callback_data="emotion:😰 Стресс"
                ),
                InlineKeyboardButton(
                    text="😐 Скука",
                    callback_data="emotion:😐 Скука"
                )
            ],
            [
                InlineKeyboardButton(
                    text="😠 Злость",
                    callback_data="emotion:😠 Злость"
                ),
                InlineKeyboardButton(
                    text="😫 Усталость",
                    callback_data="emotion:😫 Усталость"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🥪 Голод",
                    callback_data="emotion:🥪 Голод"
                ),
                InlineKeyboardButton(
                    text="🐺 Одиночество",
                    callback_data="emotion:🐺 Одиночество"
                )
            ],
            [
                InlineKeyboardButton(
                    text="✏️ Другое",
                    callback_data="emotion:custom"
                )
            ]
        ]
    )


def get_location_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора места"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🏠 Дом",
                    callback_data="location:🏠 Дом"
                ),
                InlineKeyboardButton(
                    text="🏢 Работа",
                    callback_data="location:🏢 Работа"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🍷 Бар/Тусовка",
                    callback_data="location:🍷 Бар/Тусовка"
                ),
                InlineKeyboardButton(
                    text="🚶 Улица",
                    callback_data="location:🚶 Улица"
                )
            ],
            [
                InlineKeyboardButton(
                    text="✏️ Другое",
                    callback_data="location:custom"
                )
            ]
        ]
    )


def get_company_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора компании"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="👤 Один",
                    callback_data="company:👤 Один"
                ),
                InlineKeyboardButton(
                    text="💼 Коллеги",
                    callback_data="company:💼 Коллеги"
                )
            ],
            [
                InlineKeyboardButton(
                    text="👫 Друзья",
                    callback_data="company:👫 Друзья"
                ),
                InlineKeyboardButton(
                    text="👪 Семья",
                    callback_data="company:👪 Семья"
                )
            ],
            [
                InlineKeyboardButton(
                    text="✏️ Другое",
                    callback_data="company:custom"
                )
            ]
        ]
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
