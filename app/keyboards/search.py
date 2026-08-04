from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)


PAGE_SIZE = 20


def build_search_keyboard(
    books: list[dict],
    page: int,
) -> InlineKeyboardMarkup:
    start = page * PAGE_SIZE
    end = min(start + PAGE_SIZE, len(books))

    rows = []

    for index in range(start, end):
        book = books[index]

        title = book["title"]
        author = book["author"]

        label = f"{title} — {author}"

        # Ограничиваем только текст кнопки.
        # Название скачанного файла не меняется.
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

    if end < len(books):
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