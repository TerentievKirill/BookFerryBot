import logging

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove

from app.api_client import (
    BookFerryApiError,
    get_telegram_user,
)


router = Router(name="start")
logger = logging.getLogger(__name__)


@router.message(CommandStart())
async def handle_start(
    message: Message,
    state: FSMContext,
) -> None:
    await state.clear()

    user = message.from_user

    if user is None:
        await message.answer(
            "Не удалось определить пользователя Telegram."
        )
        return

    logger.info(
        "Получена команда /start: "
        "telegram_id=%s, username=%s",
        user.id,
        user.username,
    )

    try:
        profile = await get_telegram_user(user.id)
    except BookFerryApiError as error:
        logger.exception(
            "Ошибка обращения к BookFerry Server"
        )
        await message.answer(
            f"Не удалось проверить настройки.\n\n{error}",
            reply_markup=ReplyKeyboardRemove(),
        )
        return

    if profile is None:
        await message.answer(
            "Привет! Это BookFerry 📚\n\n"
            "Я помогу найти книгу, скачать EPUB и отправить его "
            "прямо в Telegram и на электронную книгу по email.\n\n"
            "Чтобы начать, откройте Menu рядом с полем ввода "
            "и выберите «Мастер настройки».\n\n"
            "После настройки просто отправьте название или автора книги.",
            reply_markup=ReplyKeyboardRemove(),
        )
        return

    if not profile.get("emails"):
        await message.answer(
            f"Привет, {user.first_name}! 👋\n\n"
            "Настройка BookFerry ещё не завершена.\n"
            "Откройте Menu → «Мастер настройки».",
            reply_markup=ReplyKeyboardRemove(),
        )
        return

    await message.answer(
        f"С возвращением, {user.first_name}! 👋\n\n"
        "Просто отправьте название или автора книги.\n"
        "Настройки и смена библиотеки доступны через Menu.",
        reply_markup=ReplyKeyboardRemove(),
    )
