import logging

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    BufferedInputFile,
    CallbackQuery,
    Message,
)

from app.api_client import (
    BookFerryApiError,
    download_book,
    search_books,
)
from app.keyboards.search import (
    PAGE_SIZE,
    build_search_keyboard,
)


router = Router(name="search")
logger = logging.getLogger(__name__)


def build_page_text(
    books_count: int,
    page: int,
) -> str:
    pages_count = (
        books_count + PAGE_SIZE - 1
    ) // PAGE_SIZE

    return (
        f"Найдено книг: {books_count}\n"
        f"Страница {page + 1} из {pages_count}\n\n"
        "Нажмите на нужную книгу."
    )


@router.message(
    StateFilter(None),
    F.text,
)
async def handle_search(
    message: Message,
    state: FSMContext,
) -> None:
    query = message.text.strip()

    # Команды не считаем названиями книг.
    if not query or query.startswith("/"):
        return

    user = message.from_user

    if user is None:
        return

    status_message = await message.answer(
        f"Ищу: {query}"
    )

    try:
        books = await search_books(
            telegram_id=user.id,
            query=query,
        )
    except BookFerryApiError as error:
        logger.exception("Ошибка поиска")

        await status_message.edit_text(
            str(error)
        )
        return

    if not books:
        await status_message.edit_text(
            f"По запросу «{query}» ничего не найдено."
        )
        return

    await state.update_data(
        books=books,
    )

    await status_message.edit_text(
        build_page_text(
            books_count=len(books),
            page=0,
        ),
        reply_markup=build_search_keyboard(
            books=books,
            page=0,
        ),
    )


@router.callback_query(
    F.data.startswith("page:")
)
async def handle_page(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    await callback.answer()

    if callback.message is None:
        return

    data = await state.get_data()
    books = data.get("books")

    if not books:
        await callback.message.answer(
            "Результаты поиска устарели. "
            "Введите название ещё раз."
        )
        return

    page = int(callback.data.split(":")[1])

    await callback.message.edit_text(
        build_page_text(
            books_count=len(books),
            page=page,
        ),
        reply_markup=build_search_keyboard(
            books=books,
            page=page,
        ),
    )


@router.callback_query(
    F.data.startswith("book:")
)
async def handle_book(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    await callback.answer(
        "Скачиваю книгу..."
    )

    data = await state.get_data()
    books = data.get("books")

    if not books:
        await callback.bot.send_message(
            chat_id=callback.from_user.id,
            text=(
                "Результаты поиска устарели. "
                "Введите название ещё раз."
            ),
        )
        return

    try:
        index = int(callback.data.split(":")[1])
        book = books[index]
    except (IndexError, ValueError):
        await callback.bot.send_message(
            chat_id=callback.from_user.id,
            text="Не удалось определить книгу.",
        )
        return

    try:
        file_content, filename = await download_book(
            telegram_id=callback.from_user.id,
            url=book["url"],
        )
    except BookFerryApiError as error:
        logger.exception(
            "Ошибка получения книги"
        )

        await callback.bot.send_message(
            chat_id=callback.from_user.id,
            text=str(error),
        )
        return

    document = BufferedInputFile(
        file=file_content,
        filename=filename,
    )

    await callback.bot.send_document(
        chat_id=callback.from_user.id,
        document=document,
        caption=(
            f"{book['title']} — {book['author']}\n\n"
            "Книга также отправлена на email ✅"
        ),
    )