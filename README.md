# BookFerry Bot

Telegram-РёРЅС‚РµСЂС„РµР№СЃ РґР»СЏ BookFerry Server.

## Р›РѕРєР°Р»СЊРЅС‹Р№ Р·Р°РїСѓСЃРє

1. РЎРѕР·РґР°С‚СЊ РІРёСЂС‚СѓР°Р»СЊРЅРѕРµ РѕРєСЂСѓР¶РµРЅРёРµ:

   python -m venv .venv

2. РђРєС‚РёРІРёСЂРѕРІР°С‚СЊ:

   .\.venv\Scripts\Activate.ps1

3. РЈСЃС‚Р°РЅРѕРІРёС‚СЊ Р·Р°РІРёСЃРёРјРѕСЃС‚Рё:

   pip install -r requirements.txt

4. РЎРєРѕРїРёСЂРѕРІР°С‚СЊ РЅР°СЃС‚СЂРѕР№РєРё:

   Copy-Item .env.example .env

5. Р’СЃС‚Р°РІРёС‚СЊ BOT_TOKEN РІ `.env`.

6. Р—Р°РїСѓСЃС‚РёС‚СЊ:

   python main.py

## Р—Р°РїСѓСЃРє РІ Docker

docker compose up -d --build

Р›РѕРіРё:

docker compose logs -f
