import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, MenuButtonCommands

from app.config import settings
from app.handlers.about import router as about_router
from app.handlers.catalog import router as catalog_router
from app.handlers.help import router as help_router
from app.handlers.profile import router as profile_router
from app.handlers.search import router as search_router
from app.handlers.settings import router as settings_router
from app.handlers.start import router as start_router
from app.logging_config import (
    TelegramLoggingMiddleware,
    configure_logging,
)


async def configure_bot_menu(bot: Bot) -> None:
    await bot.set_my_commands(
        [
            BotCommand(
                command="settings",
                description="Мастер Настройки",
            ),
            BotCommand(
                command="catalog",
                description="Сменить каталог",
            ),
            BotCommand(
                command="profile",
                description="Профиль",
            ),
            BotCommand(
                command="help",
                description="Помощь",
            ),
            BotCommand(
                command="about",
                description="О проекте",
            ),
        ]
    )
    await bot.set_chat_menu_button(
        menu_button=MenuButtonCommands(),
    )


async def main() -> None:
    configure_logging()

    bot = Bot(token=settings.bot_token)

    dispatcher = Dispatcher(
        storage=MemoryStorage(),
    )

    dispatcher.update.outer_middleware(
        TelegramLoggingMiddleware()
    )

    dispatcher.include_router(start_router)
    dispatcher.include_router(help_router)
    dispatcher.include_router(about_router)
    dispatcher.include_router(profile_router)
    dispatcher.include_router(catalog_router)
    dispatcher.include_router(settings_router)
    dispatcher.include_router(search_router)

    await configure_bot_menu(bot)

    logging.getLogger("bookferry.bot").info(
        "BOT_STARTED polling=true"
    )

    try:
        await dispatcher.start_polling(bot)
    finally:
        logging.getLogger("bookferry.bot").info(
            "BOT_STOPPING"
        )
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.getLogger("bookferry.bot").info(
            "BOT_STOPPED reason=keyboard_interrupt"
        )
