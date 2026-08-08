from aiogram.types import (
    KeyboardButton,
    ReplyKeyboardMarkup,
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
