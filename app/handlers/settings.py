import logging
import re
from urllib.parse import urlparse

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message,
    ReplyKeyboardRemove,
)

from app.api_client import (
    BookFerryApiError,
    update_emails,
    update_opds,
    update_subject,
)
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


@router.message(Command("setting"))
@router.message(F.text == "⚙️ Настройки")
async def start_settings(
    message: Message,
    state: FSMContext,
) -> None:
    await state.set_state(SettingsState.opds)

    await message.answer(
        "Введите адрес OPDS-каталога.\n\n"
        "Например:\n"
        "https://flibusta.is/opds/",
        reply_markup=ReplyKeyboardRemove(),
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
            "Адрес должен начинаться с http:// или https://\n"
            "Например: https://flibusta.is/opds/"
        )
        return

    try:
        await update_opds(
            telegram_id=user.id,
            opds_url=opds_url,
        )
    except BookFerryApiError as error:
        logger.exception(
            "Не удалось сохранить OPDS"
        )

        await message.answer(
            f"Не удалось сохранить каталог.\n\n{error}"
        )
        return

    await state.set_state(SettingsState.emails)

    await message.answer(
        "Каталог сохранён.\n\n"
        "Теперь введите email электронной книги.\n\n"
        "Несколько адресов можно указать через запятую."
    )


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
        logger.exception(
            "Не удалось сохранить email"
        )

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
        logger.exception(
            "Не удалось очистить тему письма"
        )

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
        logger.exception(
            "Не удалось сохранить тему письма"
        )

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