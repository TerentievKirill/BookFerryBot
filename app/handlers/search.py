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
    build_search_keyboard,
)


router = Router(name="search")
logger = logging.getLogger(__name__)


def build_page_text(
    books_count: int,
    page: int,
) -> str:
    return (
        f"Книг на странице: {books_count}\n"
        f"Страница {page + 1}\n\n"
        "Нажмите на нужную книгу."
    )


async def show_search_page(
    message: Message,
    books: list[dict],
    page: int,
    has_more: bool,
) -> None:
    await message.edit_text(
        build_page_text(
            books_count=len(books),
            page=page,
        ),
        reply_markup=build_search_keyboard(
            books=books,
            page=page,
            has_more=has_more,
        ),
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

    if not query or query.startswith("/"):
        return

    user = message.from_user

    if user is None:
        return

    status_message = await message.answer(
        f"Ищу: {query}"
    )

    try:
        result = await search_books(
            telegram_id=user.id,
            query=query,
        )
    except BookFerryApiError as error:
        logger.exception("Ошибка поиска")
        await status_message.edit_text(str(error))
        return

    books = result["books"]
    next_page_url = result.get("next_page_url")

    if not books:
        await status_message.edit_text(
            f"По запросу «{query}» ничего не найдено."
        )
        return

    pages = [books]

    await state.update_data(
        query=query,
        pages=pages,
        current_page=0,
        next_page_url=next_page_url,
    )

    await show_search_page(
        message=status_message,
        books=books,
        page=0,
        has_more=next_page_url is not None,
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

    query = data.get("query")
    pages = data.get("pages")
    next_page_url = data.get("next_page_url")

    if not query or not pages:
        await callback.message.answer(
            "Результаты поиска устарели. "
            "Введите название ещё раз."
        )
        return

    try:
        page = int(callback.data.split(":")[1])
    except (IndexError, ValueError):
        return

    if page < 0:
        return

    if page < len(pages):
        page_books = pages[page]

    elif page == len(pages) and next_page_url:
        current_page_url = next_page_url

        try:
            result = await search_books(
                telegram_id=callback.from_user.id,
                query=query,
                page_url=current_page_url,
            )
        except BookFerryApiError as error:
            logger.exception(
                "Ошибка загрузки следующей страницы"
            )
            await callback.message.answer(str(error))
            return

        page_books = result["books"]
        new_next_page_url = result.get("next_page_url")

        if new_next_page_url == current_page_url:
            next_page_url = None
        else:
            next_page_url = new_next_page_url

        pages.append(page_books)

    else:
        await callback.message.answer(
            "Больше книг нет."
        )
        return

    has_more = (
        page < len(pages) - 1
        or next_page_url is not None
    )

    await state.update_data(
        pages=pages,
        current_page=page,
        next_page_url=next_page_url,
    )

    await show_search_page(
        message=callback.message,
        books=page_books,
        page=page,
        has_more=has_more,
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

    pages = data.get("pages")
    current_page = data.get("current_page", 0)

    if not pages or current_page >= len(pages):
        await callback.bot.send_message(
            chat_id=callback.from_user.id,
            text=(
                "Результаты поиска устарели. "
                "Введите название ещё раз."
            ),
        )
        return

    books = pages[current_page]

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
            f"{book['title']} — "
            f"{book['author']}\n\n"
            "Книга также отправлена "
            "на email ✅"
        ),
    )
