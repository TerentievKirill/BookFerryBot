import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove

from app.api_client import (
    BookFerryApiError,
    get_telegram_user,
)


router = Router(name="profile")
logger = logging.getLogger(__name__)


@router.message(Command("profile"))
async def handle_profile(
    message: Message,
    state: FSMContext,
) -> None:
    await state.clear()

    user = message.from_user

    if user is None:
        await message.answer(
            "Не удалось определить пользователя Telegram.",
            reply_markup=ReplyKeyboardRemove(),
        )
        return

    try:
        profile = await get_telegram_user(
            telegram_id=user.id,
        )
    except BookFerryApiError as error:
        logger.exception(
            "Не удалось получить профиль"
        )

        await message.answer(
            f"Не удалось получить настройки.\n\n{error}",
            reply_markup=ReplyKeyboardRemove(),
        )
        return

    if profile is None:
        await message.answer(
            "Настройки ещё не созданы.\n\n"
            "Чтобы настроить бота, используйте /setting",
            reply_markup=ReplyKeyboardRemove(),
        )
        return

    opds_url = (
        profile.get("opds_url")
        or "не настроен"
    )
    emails = (
        profile.get("emails")
        or "не настроен"
    )
    subject = (
        profile.get("subject")
        or "не указана"
    )

    await message.answer(
        "Ваши настройки:\n\n"
        f"OPDS: {opds_url}\n"
        f"Email: {emails}\n"
        f"Тема письма: {subject}\n\n"
        "Чтобы изменить настройки, используйте /setting",
        reply_markup=ReplyKeyboardRemove(),
    )
