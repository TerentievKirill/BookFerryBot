from aiogram.types import (
    KeyboardButton,
    ReplyKeyboardMarkup,
)


setup_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(
                text="⚙️ Настройки",
            ),
        ],
    ],
    resize_keyboard=True,
)


skip_subject_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(
                text="Пропустить",
            ),
        ],
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
)