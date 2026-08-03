# BookFerry Bot

Telegram-интерфейс для BookFerry Server.

## Локальный запуск

1. Создать виртуальное окружение:

   python -m venv .venv

2. Активировать:

   .\.venv\Scripts\Activate.ps1

3. Установить зависимости:

   pip install -r requirements.txt

4. Создать `.env` и указать `BOT_TOKEN`.

5. Запустить:

   python main.py

## Запуск в Docker

docker compose up -d --build

Логи:

docker compose logs -f
