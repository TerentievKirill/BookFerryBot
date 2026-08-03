import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    bot_token: str


def load_settings() -> Settings:
    bot_token = os.getenv("BOT_TOKEN", "").strip()

    if not bot_token:
        raise RuntimeError(
            "РќРµ Р·Р°РґР°РЅ BOT_TOKEN. "
            "Р”РѕР±Р°РІСЊС‚Рµ С‚РѕРєРµРЅ Telegram-Р±РѕС‚Р° РІ С„Р°Р№Р» .env"
        )

    return Settings(bot_token=bot_token)


settings = load_settings()
