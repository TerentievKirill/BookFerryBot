from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)


def build_catalogs_keyboard(
    catalogs: list[dict],
    *,
    callback_prefix: str = "settings_catalog",
    custom_callback: str = "settings_custom_opds",
) -> InlineKeyboardMarkup:
    rows = []

    for catalog in catalogs:
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"📚 {catalog['name']}",
                    callback_data=(
                        f"{callback_prefix}:{catalog['id']}"
                    ),
                )
            ]
        )

    rows.append(
        [
            InlineKeyboardButton(
                text="➕ Другой OPDS",
                callback_data=custom_callback,
            )
        ]
    )

    return InlineKeyboardMarkup(
        inline_keyboard=rows,
    )
