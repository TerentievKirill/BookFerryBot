import logging
from urllib.parse import urlparse

from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove

from app.api_client import (
    BookFerryApiError,
    get_catalogs,
    update_catalog,
    update_opds,
)
from app.keyboards.catalogs import build_catalogs_keyboard
from app.logging_config import current_request_id, log_event
from app.states import CatalogState


router = Router(name="catalog")
logger = logging.getLogger("bookferry.catalog")


def _is_valid_opds_url(value: str) -> bool:
    if not value or any(char.isspace() for char in value):
        return False

    parsed = urlparse(value)
    return (
        parsed.scheme in {"http", "https"}
        and bool(parsed.netloc)
    )


async def _available_catalogs() -> list[dict]:
    return [
        catalog
        for catalog in await get_catalogs()
        if catalog.get("enabled", True)
    ]


@router.message(Command("catalog"))
async def start_catalog_change(
    message: Message,
    state: FSMContext,
) -> None:
    await state.clear()

    log_event(
        logger,
        "CATALOG_MENU",
        user=message.from_user,
    )

    try:
        catalogs = await _available_catalogs()
    except BookFerryApiError as error:
        logger.exception(
            "request_id=%s CATALOG_MENU_ERROR telegram_id=%s error=%s",
            current_request_id(),
            message.from_user.id if message.from_user else "-",
            error,
        )
        await message.answer(
            f"Не удалось получить список библиотек.\n\n{error}",
            reply_markup=ReplyKeyboardRemove(),
        )
        return

    if not catalogs:
        await message.answer(
            "Сейчас нет доступных библиотек.",
            reply_markup=ReplyKeyboardRemove(),
        )
        return

    await state.update_data(
        catalog_names={
            str(catalog["id"]): catalog["name"]
            for catalog in catalogs
        }
    )

    await message.answer(
        "📚 Смена библиотеки\n\n"
        "Выберите библиотеку для поиска книг.",
        reply_markup=build_catalogs_keyboard(
            catalogs,
            callback_prefix="catalog_select",
            custom_callback="catalog_custom_opds",
        ),
    )


@router.callback_query(F.data.startswith("catalog_select:"))
async def select_catalog(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    await callback.answer()

    try:
        catalog_id = int(callback.data.split(":", 1)[1])
    except (AttributeError, IndexError, ValueError):
        return

    data = await state.get_data()
    catalog_name = data.get("catalog_names", {}).get(
        str(catalog_id),
        "выбранную библиотеку",
    )

    log_event(
        logger,
        "CATALOG_CHANGE",
        user=callback.from_user,
        catalog_id=catalog_id,
        catalog=catalog_name,
    )

    try:
        await update_catalog(
            telegram_id=callback.from_user.id,
            catalog_id=catalog_id,
        )
    except BookFerryApiError as error:
        logger.exception(
            "request_id=%s CATALOG_CHANGE_ERROR telegram_id=%s catalog_id=%s error=%s",
            current_request_id(),
            callback.from_user.id,
            catalog_id,
            error,
        )
        if callback.message:
            await callback.message.answer(
                f"Не удалось сменить библиотеку.\n\n{error}"
            )
        return

    await state.clear()

    log_event(
        logger,
        "CATALOG_CHANGE_RESULT",
        user=callback.from_user,
        catalog_id=catalog_id,
        catalog=catalog_name,
        result="success",
    )

    if callback.message:
        await callback.message.edit_text(
            f"✅ Библиотека изменена: {catalog_name}\n\n"
            "Теперь просто отправьте название или автора книги."
        )


@router.callback_query(F.data == "catalog_custom_opds")
async def select_custom_opds(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    await callback.answer()
    await state.set_state(CatalogState.opds)

    log_event(
        logger,
        "CUSTOM_OPDS_INPUT",
        user=callback.from_user,
    )

    if callback.message:
        await callback.message.edit_text(
            "🌐 Другой OPDS\n\n"
            "Отправьте адрес OPDS-каталога.\n"
            "BookFerry проверит его перед сохранением."
        )


@router.message(
    StateFilter(CatalogState.opds),
    F.text,
    ~F.text.startswith("/"),
)
async def save_custom_opds(
    message: Message,
    state: FSMContext,
) -> None:
    user = message.from_user
    opds_url = message.text.strip()

    if user is None:
        await message.answer("Не удалось определить пользователя Telegram.")
        return

    if not _is_valid_opds_url(opds_url):
        await message.answer(
            "Адрес должен начинаться с http:// или https://"
        )
        return

    log_event(
        logger,
        "CUSTOM_OPDS_CHANGE",
        user=user,
        opds_url=opds_url,
    )

    status_message = await message.answer("Проверяю OPDS-каталог…")

    try:
        await update_opds(
            telegram_id=user.id,
            opds_url=opds_url,
        )
    except BookFerryApiError as error:
        logger.exception(
            "request_id=%s CUSTOM_OPDS_ERROR telegram_id=%s opds_url=%r error=%s",
            current_request_id(),
            user.id,
            opds_url,
            error,
        )
        await status_message.edit_text(
            f"Не удалось подключить OPDS-каталог.\n\n{error}"
        )
        return

    await state.clear()

    log_event(
        logger,
        "CUSTOM_OPDS_RESULT",
        user=user,
        opds_url=opds_url,
        result="success",
    )

    await status_message.edit_text(
        "✅ Пользовательский OPDS подключён.\n\n"
        "Теперь просто отправьте название или автора книги."
    )
