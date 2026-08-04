import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from app.handlers.search import router as search_router
from app.config import settings
from app.handlers.settings import (
    router as settings_router,
)
from app.handlers.start import (
    router as start_router,
)


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s | %(levelname)s | "
            "%(name)s | %(message)s"
        ),
    )

    bot = Bot(token=settings.bot_token)

    dispatcher = Dispatcher(
        storage=MemoryStorage(),
    )

    dispatcher.include_router(start_router)
    dispatcher.include_router(settings_router)
    dispatcher.include_router(search_router)

    logging.info("BookFerry Bot запущен")

    try:
        await dispatcher.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("BookFerry Bot остановлен")