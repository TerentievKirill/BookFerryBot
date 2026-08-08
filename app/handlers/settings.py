import logging
import re
from urllib.parse import urlparse

from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    Message,
    ReplyKeyboardRemove,
)

from app.api_client import (
    BookFerryApiError,
    get_catalogs,
    update_catalog,
    update_emails,
    update_opds,
    update_subject,
)
from app.keyboards.catalogs import build_catalogs_keyboard
from app.keyboards.reply import skip_subject_keyboard
from app.states import SettingsState


router = Router(name="settings")
logger = logging.getLogger(__name__)

MAX_EMAILS = 5
MAX_SUBJECT_LENGTH = 200
EMAIL_PATTERN = re.compile(
    r"^[^@\s,]+@[^@\s,]+\.[^@\s,]+$"
)


def is_valid_opds_url(value: str) -> bool:
    if not value or any(char.isspace() for char in value):
        return False

    parsed = urlparse(value)

    return (
        parsed.scheme in {"http", "https"}
        and bool(parsed.netloc)
    )


def normalize_emails(value: str) -> tuple[str | None, str | None]:
    emails = [
        email.strip()
        for email in value.split(",")
        if email.strip()
    ]

    if not emails:
        return None, "Email не может быть пустым."

    if len(emails) > MAX_EMAILS:
        return None, (
            f"Можно указать не больше {MAX_EMAILS} адресов."
        )

    invalid_emails = [
        email
        for email in emails
        if not EMAIL_PATTERN.fullmatch(email)
    ]

    if invalid_emails:
        return None, (
            "Проверьте адрес email:\n"
            + "\n".join(invalid_emails)
        )

    unique_emails = list(dict.fromkeys(emails))

    return ", ".join(unique_emails), None


async def _ask_emails(message: Message) -> None:
    await message.answer(
        "Теперь введите email электронной книги.\n\n"
        "Несколько адресов можно указать через запятую.",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(Command("setting"))
@router.message(F.text == "⚙️ Настройки")
async def start_settings(
    message: Message,
    state: FSMContext,
) -> None:
    await state.clear()

    try:
        catalogs = [
            catalog
            for catalog in await get_catalogs()
            if catalog.get("enabled", True)
        ]
    except BookFerryApiError as error:
        logger.exception("Не удалось получить каталоги")
        await message.answer(
            f"Не удалось получить список каталогов.\n\n{error}",
            reply_markup=ReplyKeyboardRemove(),
        )
        return

    if not catalogs:
        await message.answer(
            "На сервере сейчас нет доступных каталогов.",
            reply_markup=ReplyKeyboardRemove(),
        )
        return

    await state.update_data(
        catalog_names={
            str(catalog["id"]): catalog["name"]
            for catalog in catalogs
        }
    )
    await state.set_state(SettingsState.catalog)

    await message.answer(
        "Выберите каталог.\n\n"
        "Встроенные каталоги ищут по быстрому локальному индексу. "
        "Если нужного каталога нет — выберите «Другой OPDS».",
        reply_markup=build_catalogs_keyboard(catalogs),
    )


@router.callback_query(
    StateFilter(SettingsState.catalog),
    F.data.startswith("settings_catalog:"),
)
async def process_catalog(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    await callback.answer()

    try:
        catalog_id = int(callback.data.split(":", 1)[1])
    except (AttributeError, IndexError, ValueError):
        return

    try:
        await update_catalog(
            telegram_id=callback.from_user.id,
            catalog_id=catalog_id,
        )
    except BookFerryApiError as error:
        logger.exception("Не удалось сохранить каталог")
        if callback.message:
            await callback.message.answer(
                f"Не удалось сохранить каталог.\n\n{error}"
            )
        return

    data = await state.get_data()
    catalog_name = data.get("catalog_names", {}).get(
        str(catalog_id),
        "выбран",
    )

    await state.set_state(SettingsState.emails)

    if callback.message:
        await callback.message.edit_text(
            f"Каталог сохранён: {catalog_name} ✅"
        )
        await _ask_emails(callback.message)


@router.callback_query(
    StateFilter(SettingsState.catalog),
    F.data == "settings_custom_opds",
)
async def process_custom_catalog(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    await callback.answer()
    await state.set_state(SettingsState.opds)

    if callback.message:
        await callback.message.edit_text(
            "Введите адрес своего OPDS-каталога.\n\n"
            "BookFerry проверит адрес и наличие поиска.\n\n"
            "Например:\n"
            "https://example.org/opds"
        )


@router.message(SettingsState.catalog)
async def process_invalid_catalog(
    message: Message,
) -> None:
    await message.answer(
        "Выберите каталог кнопкой выше или нажмите «Другой OPDS»."
    )


@router.message(SettingsState.opds, F.text)
async def process_opds(
    message: Message,
    state: FSMContext,
) -> None:
    user = message.from_user
    opds_url = message.text.strip()

    if user is None:
        await message.answer(
            "Не удалось определить пользователя Telegram."
        )
        return

    if not is_valid_opds_url(opds_url):
        await message.answer(
            "Некорректный адрес OPDS-каталога.\n\n"
            "Адрес должен начинаться с http:// или https://"
        )
        return

    status_message = await message.answer(
        "Проверяю OPDS-каталог..."
    )

    try:
        await update_opds(
            telegram_id=user.id,
            opds_url=opds_url,
        )
    except BookFerryApiError as error:
        logger.exception("Не удалось сохранить OPDS")
        await status_message.edit_text(
            f"Не удалось подключить каталог.\n\n{error}"
        )
        return

    await state.set_state(SettingsState.emails)

    await status_message.edit_text(
        "OPDS-каталог проверен и сохранён ✅"
    )
    await _ask_emails(message)


@router.message(SettingsState.opds)
async def process_invalid_opds(
    message: Message,
) -> None:
    await message.answer(
        "Отправьте адрес OPDS-каталога обычным текстом."
    )


@router.message(SettingsState.emails, F.text)
async def process_emails(
    message: Message,
    state: FSMContext,
) -> None:
    user = message.from_user
    emails, validation_error = normalize_emails(
        message.text.strip()
    )

    if user is None:
        await message.answer(
            "Не удалось определить пользователя Telegram."
        )
        return

    if validation_error:
        await message.answer(validation_error)
        return

    try:
        await update_emails(
            telegram_id=user.id,
            emails=emails,
        )
    except BookFerryApiError as error:
        logger.exception("Не удалось сохранить email")
        await message.answer(
            f"Не удалось сохранить email.\n\n{error}"
        )
        return

    await state.set_state(SettingsState.subject)

    await message.answer(
        "Email сохранён.\n\n"
        "Введите тему письма или нажмите «Пропустить».",
        reply_markup=skip_subject_keyboard,
    )


@router.message(SettingsState.emails)
async def process_invalid_emails(
    message: Message,
) -> None:
    await message.answer(
        "Отправьте email обычным текстом.\n"
        "Несколько адресов укажите через запятую."
    )


@router.message(
    SettingsState.subject,
    F.text == "Пропустить",
)
async def skip_subject(
    message: Message,
    state: FSMContext,
) -> None:
    user = message.from_user

    if user is None:
        await message.answer(
            "Не удалось определить пользователя Telegram."
        )
        return

    try:
        await update_subject(
            telegram_id=user.id,
            subject=None,
        )
    except BookFerryApiError as error:
        logger.exception("Не удалось очистить тему письма")
        await message.answer(
            f"Не удалось сохранить настройки.\n\n{error}"
        )
        return

    await state.clear()

    await message.answer(
        "Настройка завершена ✅\n\n"
        "Теперь просто отправьте название книги.",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(SettingsState.subject, F.text)
async def process_subject(
    message: Message,
    state: FSMContext,
) -> None:
    user = message.from_user
    subject = message.text.strip()

    if user is None:
        await message.answer(
            "Не удалось определить пользователя Telegram."
        )
        return

    if len(subject) > MAX_SUBJECT_LENGTH:
        await message.answer(
            "Тема слишком длинная. "
            f"Максимум {MAX_SUBJECT_LENGTH} символов."
        )
        return

    try:
        await update_subject(
            telegram_id=user.id,
            subject=subject or None,
        )
    except BookFerryApiError as error:
        logger.exception("Не удалось сохранить тему письма")
        await message.answer(
            f"Не удалось сохранить тему.\n\n{error}"
        )
        return

    await state.clear()

    await message.answer(
        "Настройка завершена ✅\n\n"
        "Теперь просто отправьте название книги.",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(SettingsState.subject)
async def process_invalid_subject(
    message: Message,
) -> None:
    await message.answer(
        "Отправьте тему письма обычным текстом "
        "или нажмите «Пропустить»."
    )
