from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)


def build_search_keyboard(
    books: list[dict],
    page: int,
    has_more: bool,
) -> InlineKeyboardMarkup:
    rows = []

    for index, book in enumerate(books):
        title = book["title"]
        author = book["author"]

        label = f"{title} — {author}"

        if len(label) > 64:
            label = label[:61] + "..."

        rows.append(
            [
                InlineKeyboardButton(
                    text=label,
                    callback_data=f"book:{index}",
                )
            ]
        )

    navigation = []

    if page > 0:
        navigation.append(
            InlineKeyboardButton(
                text="← Назад",
                callback_data=f"page:{page - 1}",
            )
        )

    if has_more:
        navigation.append(
            InlineKeyboardButton(
                text="Далее →",
                callback_data=f"page:{page + 1}",
            )
        )

    if navigation:
        rows.append(navigation)

    return InlineKeyboardMarkup(
        inline_keyboard=rows,
    )
