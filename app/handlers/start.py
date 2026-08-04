import logging

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove

from app.api_client import (
    BookFerryApiError,
    get_telegram_user,
)
from app.keyboards.reply import setup_keyboard


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
            f"Не удалось проверить настройки.\n\n{error}"
        )
        return

    if profile is None:
        await message.answer(
            f"Привет, {user.first_name}! 👋\n\n"
            "Я BookFerry — помогу найти книгу "
            "и отправить её на электронную книгу.\n\n"
            "Для начала нужно выполнить настройку.",
            reply_markup=setup_keyboard,
        )
        return

    if not profile.get("emails"):
        await message.answer(
            f"Привет, {user.first_name}! 👋\n\n"
            "Настройка BookFerry ещё не завершена.",
            reply_markup=setup_keyboard,
        )
        return

    await message.answer(
        f"С возвращением, {user.first_name}! 👋\n\n"
        "Просто отправьте название книги.",
        reply_markup=ReplyKeyboardRemove(),
    )
