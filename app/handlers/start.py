import logging

from aiogram import Router
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
            "Привет! Это BookFerry 📚\n\n"
            "Я помогу найти книгу, скачать её в EPUB и отправить:\n\n"
            "• прямо в Telegram;\n"
            "• на вашу электронную книгу по email.\n\n"
            "Можно выбрать один из встроенных каталогов BookFerry "
            "или подключить свой OPDS.\n\n"
            "Для начала выполните /setting.\n\n"
            "После настройки просто отправьте название книги.\n\n"
            "Ваши текущие настройки: /profile\n"
            "Подробная инструкция: /help\n\n"
            "Если вы используете PocketBook, после первой отправки "
            "может прийти письмо с подтверждением. Добавьте адрес "
            "отправителя BookFerry в список доверенных отправителей "
            "Send-to-PocketBook — после этого книги будут поступать "
            "на устройство автоматически.",
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
