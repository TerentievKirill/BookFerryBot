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
from app.logging_config import current_request_id, log_event
from app.states import SettingsState


router = Router(name="settings")
logger = logging.getLogger("bookferry.settings")

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
        "Шаг 2 из 3 — email 📧\n\n"
        "Введите email электронной книги.\n"
        "Можно указать до пяти адресов через запятую.",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(Command("settings"))
@router.message(Command("setting"))
async def start_settings(
    message: Message,
    state: FSMContext,
) -> None:
    await state.clear()

    log_event(
        logger,
        "SETTINGS_START",
        user=message.from_user,
    )

    try:
        catalogs = [
            catalog
            for catalog in await get_catalogs()
            if catalog.get("enabled", True)
        ]
    except BookFerryApiError as error:
        logger.exception(
            "request_id=%s SETTINGS_START_ERROR telegram_id=%s error=%s",
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
    await state.set_state(SettingsState.catalog)

    await message.answer(
        "⚙️ Мастер настройки BookFerry\n\n"
        "Шаг 1 из 3 — библиотека 📚\n\n"
        "Выберите библиотеку для поиска. "
        "Если нужной нет в списке, можно подключить свой OPDS.",
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

    data = await state.get_data()
    catalog_name = data.get("catalog_names", {}).get(
        str(catalog_id),
        "выбранная библиотека",
    )

    log_event(
        logger,
        "SETTINGS_CATALOG",
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
            "request_id=%s SETTINGS_CATALOG_ERROR telegram_id=%s catalog_id=%s error=%s",
            current_request_id(),
            callback.from_user.id,
            catalog_id,
            error,
        )
        if callback.message:
            await callback.message.answer(
                f"Не удалось сохранить библиотеку.\n\n{error}"
            )
        return

    await state.set_state(SettingsState.emails)

    if callback.message:
        await callback.message.edit_text(
            f"✅ Библиотека: {catalog_name}"
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

    log_event(
        logger,
        "SETTINGS_CUSTOM_OPDS_INPUT",
        user=callback.from_user,
    )

    if callback.message:
        await callback.message.edit_text(
            "🌐 Другой OPDS\n\n"
            "Отправьте адрес OPDS-каталога.\n"
            "BookFerry проверит его перед сохранением."
        )


@router.message(SettingsState.catalog)
async def process_invalid_catalog(
    message: Message,
) -> None:
    await message.answer(
        "Выберите библиотеку кнопкой выше."
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
            "Адрес должен начинаться с http:// или https://"
        )
        return

    log_event(
        logger,
        "SETTINGS_CUSTOM_OPDS",
        user=user,
        opds_url=opds_url,
    )

    status_message = await message.answer(
        "Проверяю OPDS-каталог…"
    )

    try:
        await update_opds(
            telegram_id=user.id,
            opds_url=opds_url,
        )
    except BookFerryApiError as error:
        logger.exception(
            "request_id=%s SETTINGS_CUSTOM_OPDS_ERROR telegram_id=%s opds_url=%r error=%s",
            current_request_id(),
            user.id,
            opds_url,
            error,
        )
        await status_message.edit_text(
            f"Не удалось подключить OPDS-каталог.\n\n{error}"
        )
        return

    await state.set_state(SettingsState.emails)

    await status_message.edit_text(
        "✅ Пользовательский OPDS подключён."
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

    email_count = len(
        [item for item in emails.split(",") if item.strip()]
    )

    log_event(
        logger,
        "SETTINGS_EMAILS",
        user=user,
        email_count=email_count,
    )

    try:
        await update_emails(
            telegram_id=user.id,
            emails=emails,
        )
    except BookFerryApiError as error:
        logger.exception(
            "request_id=%s SETTINGS_EMAILS_ERROR telegram_id=%s email_count=%s error=%s",
            current_request_id(),
            user.id,
            email_count,
            error,
        )
        await message.answer(
            f"Не удалось сохранить email.\n\n{error}"
        )
        return

    await state.set_state(SettingsState.subject)

    await message.answer(
        "✅ Email сохранён.\n\n"
        "Шаг 3 из 3 — тема письма ✉️\n\n"
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


async def _finish_settings(
    message: Message,
    state: FSMContext,
) -> None:
    log_event(
        logger,
        "SETTINGS_COMPLETE",
        user=message.from_user,
        result="success",
    )
    await state.clear()
    await message.answer(
        "✅ Настройка завершена.\n\n"
        "Теперь просто отправьте название или автора книги.\n"
        "Быстро сменить библиотеку можно через Menu → «Сменить каталог».",
        reply_markup=ReplyKeyboardRemove(),
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

    log_event(
        logger,
        "SETTINGS_SUBJECT",
        user=user,
        action="cleared",
    )

    try:
        await update_subject(
            telegram_id=user.id,
            subject=None,
        )
    except BookFerryApiError as error:
        logger.exception(
            "request_id=%s SETTINGS_SUBJECT_ERROR telegram_id=%s action=cleared error=%s",
            current_request_id(),
            user.id,
            error,
        )
        await message.answer(
            f"Не удалось сохранить настройки.\n\n{error}"
        )
        return

    await _finish_settings(message, state)


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

    log_event(
        logger,
        "SETTINGS_SUBJECT",
        user=user,
        action="set" if subject else "cleared",
    )

    try:
        await update_subject(
            telegram_id=user.id,
            subject=subject or None,
        )
    except BookFerryApiError as error:
        logger.exception(
            "request_id=%s SETTINGS_SUBJECT_ERROR telegram_id=%s action=%s error=%s",
            current_request_id(),
            user.id,
            "set" if subject else "cleared",
            error,
        )
        await message.answer(
            f"Не удалось сохранить тему.\n\n{error}"
        )
        return

    await _finish_settings(message, state)


@router.message(SettingsState.subject)
async def process_invalid_subject(
    message: Message,
) -> None:
    await message.answer(
        "Отправьте тему письма обычным текстом "
        "или нажмите «Пропустить»."
    )
