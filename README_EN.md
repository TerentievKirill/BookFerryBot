# BookFerry Bot

[Русский](README.md) | **English**

Telegram client for [BookFerry Server](https://github.com/TerentievKirill/BookFerry).

The bot searches for EPUB books through BookFerry, sends the selected file directly to Telegram, and can deliver the same EPUB to configured email addresses.

> **Project status: prototype.** The main user flow already works, but the interface structure, button labels and message texts may still change.

## Current capabilities

- first-run setup wizard;
- selection of a built-in book catalog;
- custom OPDS configuration;
- up to five email addresses;
- custom email subject;
- search by book title or author;
- paginated search results;
- EPUB download directly to Telegram;
- delivery of the same EPUB to configured email addresses;
- profile view and quick catalog switching.

Search and download logic lives in BookFerry Server. The bot is the Telegram-facing client and communicates with the backend through its HTTP API.

```text
Telegram user
      ↓
BookFerryBot
      ↓
BookFerry API
      ↓
book catalog / EPUB source
      ↓
Telegram + configured email
```

## Why UI texts are still in code

The project is intentionally still in the prototype stage. The user flow is being refined, so message wording, button names and even the sequence of actions may still change.

For now, button labels and user-facing messages stay close to the handlers and keyboards that use them. This makes rapid iteration easier while the interaction model is still moving. It would not be the preferred structure for a stable product, but extracting every string too early would create an extra synchronization layer around an interface that is not final yet.

Once the prototype stabilizes:

1. user-facing texts and button labels will move into dedicated resource files;
2. handlers will keep only scenario logic;
3. language selection and interface localization will be added.

So keeping texts in code is a deliberate temporary trade-off for the prototype, not the intended final architecture.

## Main commands

| Command | Purpose |
|---|---|
| `/start` | start using the bot |
| `/settings` | configuration wizard |
| `/catalog` | switch book catalog |
| `/profile` | view current user settings |
| `/help` | help |
| `/about` | project information |

After configuration, search does not require a special command: the user can simply send a book title or author name.

## Project structure

```text
BookFerryBot/
├── app/
│   ├── api_client.py
│   ├── config.py
│   ├── logging_config.py
│   ├── states.py
│   ├── handlers/
│   │   ├── start.py
│   │   ├── settings.py
│   │   ├── catalog.py
│   │   ├── profile.py
│   │   ├── search.py
│   │   ├── help.py
│   │   └── about.py
│   └── keyboards/
├── main.py
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

The bot is built with `aiogram 3`; `httpx` is used to communicate with the BookFerry API.

## Running locally

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Create `.env`:

```env
BOT_TOKEN=telegram-bot-token
API_BASE_URL=https://example.com
```

Start the bot:

```powershell
python main.py
```

## Docker

```bash
docker compose up -d --build
```

Logs:

```bash
docker compose logs -f
```
