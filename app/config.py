import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


ENV_FILE = Path(__file__).resolve().parent.parent / ".env"

load_dotenv(
    dotenv_path=ENV_FILE,
    encoding="utf-8-sig",
)


@dataclass(frozen=True)
class Settings:
    bot_token: str
    api_base_url: str


def load_settings() -> Settings:
    bot_token = os.getenv("BOT_TOKEN", "").strip()
    api_base_url = os.getenv("API_BASE_URL", "").strip().rstrip("/")

    if not bot_token:
        raise RuntimeError(
            f"Не задан BOT_TOKEN в файле {ENV_FILE}"
        )

    if not api_base_url:
        raise RuntimeError(
            f"Не задан API_BASE_URL в файле {ENV_FILE}"
        )

    return Settings(
        bot_token=bot_token,
        api_base_url=api_base_url,
    )


settings = load_settings()