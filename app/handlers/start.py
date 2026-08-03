import logging

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message


router = Router(name="start")
logger = logging.getLogger(__name__)


@router.message(CommandStart())
async def handle_start(message: Message) -> None:
    user = message.from_user

    if user is not None:
        logger.info(
            "Получена команда /start: telegram_id=%s, username=%s",
            user.id,
            user.username,
        )
        user_name = user.first_name
    else:
        user_name = "читатель"

    await message.answer(
        f"Привет, {user_name}! 👋\n\n"
        "Я BookFerry — помогу найти книгу и отправить её "
        "на электронную книгу.\n\n"
        "Бот запущен и готов к настройке."
    )
