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
            "РџРѕР»СѓС‡РµРЅР° РєРѕРјР°РЅРґР° /start: telegram_id=%s, username=%s",
            user.id,
            user.username,
        )
        user_name = user.first_name
    else:
        user_name = "С‡РёС‚Р°С‚РµР»СЊ"

    await message.answer(
        f"РџСЂРёРІРµС‚, {user_name}! рџ‘‹\n\n"
        "РЇ BookFerry вЂ” РїРѕРјРѕРіСѓ РЅР°Р№С‚Рё РєРЅРёРіСѓ Рё РѕС‚РїСЂР°РІРёС‚СЊ РµС‘ "
        "РЅР° СЌР»РµРєС‚СЂРѕРЅРЅСѓСЋ РєРЅРёРіСѓ.\n\n"
        "Р‘РѕС‚ Р·Р°РїСѓС‰РµРЅ Рё РіРѕС‚РѕРІ Рє РЅР°СЃС‚СЂРѕР№РєРµ."
    )
