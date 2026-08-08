from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)


def build_catalogs_keyboard(
    catalogs: list[dict],
) -> InlineKeyboardMarkup:
    rows = []

    for catalog in catalogs:
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"📚 {catalog['name']}",
                    callback_data=f"settings_catalog:{catalog['id']}",
                )
            ]
        )

    rows.append(
        [
            InlineKeyboardButton(
                text="➕ Другой OPDS",
                callback_data="settings_custom_opds",
            )
        ]
    )

    return InlineKeyboardMarkup(
        inline_keyboard=rows,
    )
