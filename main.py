import asyncio
import logging

from aiogram import Bot, Dispatcher

from app.config import settings
from app.handlers.start import router as start_router


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    bot = Bot(token=settings.bot_token)

    dispatcher = Dispatcher()
    dispatcher.include_router(start_router)

    logging.info("BookFerry Bot Р·Р°РїСѓС‰РµРЅ")

    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("BookFerry Bot РѕСЃС‚Р°РЅРѕРІР»РµРЅ")
