import asyncio
import os

import allure
import pytest

from app.api_client import download_book, search_books, update_catalog


TEST_TELEGRAM_ID = int(os.getenv("TEST_TELEGRAM_ID", "0"))

CATALOG_CASES = [
    pytest.param(
        1,
        "alice adams",
        "Alice Adams",
        id="gutenberg",
    ),
    pytest.param(
        20,
        "anarchism other essays",
        "Anarchism and Other Essays",
        id="anarchist",
    ),
    pytest.param(
        3,
        "лабиринт отражений",
        "Лабиринт отражений",
        id="flibusta",
    ),
    pytest.param(
        28,
        "государственность анархия",
        "Государственность и анархия",
        id="anarchist-ru",
    ),
]


# External E2E smoke test started from the BookFerry server repository.
# It intentionally stays small and checks that the main bot-to-server flow still works
# after server changes: select a catalog, find a book and download it.
def _find_book(books: list[dict], expected_title: str) -> dict:
    expected = expected_title.casefold()

    for book in books:
        if expected in book.get("title", "").casefold():
            return book

    titles = [book.get("title") for book in books]
    raise AssertionError(
        f"Book {expected_title!r} was not found. Returned titles: {titles}"
    )


async def _run_book_flow(
    catalog_id: int,
    query: str,
    expected_title: str,
) -> None:
    with allure.step(f"Select catalog: {catalog_id}"):
        await update_catalog(
            telegram_id=TEST_TELEGRAM_ID,
            catalog_id=catalog_id,
        )

    with allure.step(f"Find book: {expected_title}"):
        result = await search_books(
            telegram_id=TEST_TELEGRAM_ID,
            query=query,
        )

        book = _find_book(
            books=result["books"],
            expected_title=expected_title,
        )

    with allure.step(f"Download and validate book: {expected_title}"):
        file_content, filename = await download_book(
            telegram_id=TEST_TELEGRAM_ID,
            url=book["url"],
        )

        assert filename.lower().endswith(".epub")
        assert len(file_content) > 1000
        assert file_content.startswith(b"PK")


@pytest.mark.e2e
@allure.title("Bot can find and download book: {expected_title}")
@pytest.mark.parametrize(
    "catalog_id,query,expected_title",
    CATALOG_CASES,
)
def test_bot_can_find_and_download_book(
    catalog_id,
    query,
    expected_title,
):
    asyncio.run(
        _run_book_flow(
            catalog_id=catalog_id,
            query=query,
            expected_title=expected_title,
        )
    )
