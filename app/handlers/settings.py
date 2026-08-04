import logging

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

    if not opds_url:
        await message.answer(
            "Адрес каталога не может быть пустым."
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


@router.message(SettingsState.emails, F.text)
async def process_emails(
    message: Message,
    state: FSMContext,
) -> None:
    user = message.from_user
    emails = message.text.strip()

    if user is None:
        await message.answer(
            "Не удалось определить пользователя Telegram."
        )
        return

    if not emails:
        await message.answer(
            "Email не может быть пустым."
        )
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

    await state.clear()

    await message.answer(
        "Настройка завершена ✅\n\n"
        "Теперь просто отправьте название книги.",
        reply_markup=ReplyKeyboardRemove(),
    )