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
from app.keyboards.search import build_search_keyboard
from app.logging_config import current_request_id, log_event


router = Router(name="search")
logger = logging.getLogger("bookferry.search")


def _book_sample(books: list[dict], limit: int = 5) -> str:
    return " | ".join(
        f"{book.get('title', '')} — {book.get('author', '')}".strip(" —")
        for book in books[:limit]
    )


def build_page_text(
    books_count: int,
    page: int,
) -> str:
    return (
        f"📚 Книг на странице: {books_count}\n"
        f"Страница {page + 1}\n\n"
        "Выберите нужную книгу:"
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

    log_event(
        logger,
        "SEARCH",
        user=user,
        query=query,
        page="first",
    )

    status_message = await message.answer(
        f"🔎 Ищу: {query}"
    )

    try:
        result = await search_books(
            telegram_id=user.id,
            query=query,
        )
    except BookFerryApiError as error:
        logger.exception(
            "request_id=%s SEARCH_ERROR telegram_id=%s query=%r error=%s",
            current_request_id(),
            user.id,
            query,
            error,
        )
        await status_message.edit_text(str(error))
        return

    books = result["books"]
    next_page_url = result.get("next_page_url")

    log_event(
        logger,
        "SEARCH_RESULT",
        user=user,
        query=query,
        found=len(books),
        has_more=next_page_url is not None,
        sample=_book_sample(books),
    )

    if not books:
        await status_message.edit_text(
            f"По запросу «{query}» ничего не найдено.\n\n"
            "Попробуйте другое название, автора или смените библиотеку "
            "через Menu."
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
            "Отправьте запрос ещё раз."
        )
        return

    try:
        page = int(callback.data.split(":")[1])
    except (IndexError, ValueError):
        return

    if page < 0:
        return

    log_event(
        logger,
        "SEARCH_PAGE",
        user=callback.from_user,
        query=query,
        page=page + 1,
    )

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
                "request_id=%s SEARCH_PAGE_ERROR telegram_id=%s query=%r page=%s error=%s",
                current_request_id(),
                callback.from_user.id,
                query,
                page + 1,
                error,
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
            "Больше результатов нет."
        )
        return

    has_more = (
        page < len(pages) - 1
        or next_page_url is not None
    )

    log_event(
        logger,
        "SEARCH_PAGE_RESULT",
        user=callback.from_user,
        query=query,
        page=page + 1,
        found=len(page_books),
        has_more=has_more,
        sample=_book_sample(page_books),
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
        "Скачиваю EPUB…"
    )

    if callback.message is not None:
        await callback.message.edit_reply_markup(
            reply_markup=None,
        )

    data = await state.get_data()

    pages = data.get("pages")
    current_page = data.get("current_page", 0)

    if not pages or current_page >= len(pages):
        await callback.bot.send_message(
            chat_id=callback.from_user.id,
            text=(
                "Результаты поиска устарели. "
                "Отправьте запрос ещё раз."
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
            text="Не удалось определить выбранную книгу.",
        )
        return

    log_event(
        logger,
        "BOOK_SELECTED",
        user=callback.from_user,
        title=book.get("title"),
        author=book.get("author"),
        page=current_page + 1,
    )

    try:
        file_content, filename = await download_book(
            telegram_id=callback.from_user.id,
            url=book["url"],
        )
    except BookFerryApiError as error:
        logger.exception(
            "request_id=%s BOOK_ERROR telegram_id=%s title=%r error=%s",
            current_request_id(),
            callback.from_user.id,
            book.get("title"),
            error,
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
            "✅ EPUB также отправлен на настроенные email."
        ),
    )

    log_event(
        logger,
        "BOOK_SENT",
        user=callback.from_user,
        title=book.get("title"),
        author=book.get("author"),
        filename=filename,
        size_bytes=len(file_content),
        result="success",
    )
