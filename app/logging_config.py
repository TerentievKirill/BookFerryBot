from __future__ import annotations

import json
import logging
import re
import sys
import time
import uuid
from contextvars import ContextVar
from datetime import datetime
from typing import Any, Awaitable, Callable
from zoneinfo import ZoneInfo

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update, User


LOG_TIMEZONE = ZoneInfo("Asia/Almaty")
MAX_LOG_VALUE_LENGTH = 500
REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,64}$")

_request_id_var: ContextVar[str] = ContextVar(
    "bookferry_request_id",
    default="-",
)


class AlmatyFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        moment = datetime.fromtimestamp(
            record.created,
            tz=LOG_TIMEZONE,
        )
        if datefmt:
            return moment.strftime(datefmt)
        return moment.strftime("%Y-%m-%d %H:%M:%S%z")


def configure_logging() -> None:
    root = logging.getLogger()
    root.setLevel(logging.INFO)

    for handler in list(root.handlers):
        root.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        AlmatyFormatter(
            fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S%z",
        )
    )
    root.addHandler(handler)

    # HTTP-клиенты на INFO слишком шумные: наши API_CALL/API_RESULT полезнее.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def current_request_id() -> str:
    return _request_id_var.get()


def _clean_log_value(value: Any) -> str:
    text = str(value).replace("\r", " ").replace("\n", " ").strip()
    if len(text) > MAX_LOG_VALUE_LENGTH:
        return text[: MAX_LOG_VALUE_LENGTH - 3] + "..."
    return text


def _format_field(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    return json.dumps(_clean_log_value(value), ensure_ascii=False)


def log_event(
    logger: logging.Logger,
    event: str,
    *,
    user: User | None = None,
    **fields: Any,
) -> None:
    parts = [
        f"request_id={current_request_id()}",
        event,
    ]

    if user is not None:
        parts.append(f"telegram_id={user.id}")
        parts.append(f"username={_format_field(user.username)}")

    parts.extend(
        f"{key}={_format_field(value)}"
        for key, value in fields.items()
    )
    logger.info(" ".join(parts))


def _event_user(update: Update, data: dict[str, Any]) -> User | None:
    user = data.get("event_from_user")
    if isinstance(user, User):
        return user

    if update.message and update.message.from_user:
        return update.message.from_user
    if update.callback_query and update.callback_query.from_user:
        return update.callback_query.from_user
    if update.edited_message and update.edited_message.from_user:
        return update.edited_message.from_user
    return None


def _update_kind(update: Update) -> str:
    if update.message:
        return "message"
    if update.callback_query:
        return "callback_query"
    if update.edited_message:
        return "edited_message"
    if update.inline_query:
        return "inline_query"
    return "other"


def _command(update: Update) -> str | None:
    if not update.message or not update.message.text:
        return None
    text = update.message.text.strip()
    if not text.startswith("/"):
        return None
    return text.split(maxsplit=1)[0]


class TelegramLoggingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[
            [TelegramObject, dict[str, Any]],
            Awaitable[Any],
        ],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if not isinstance(event, Update):
            return await handler(event, data)

        request_id = uuid.uuid4().hex[:12]
        if REQUEST_ID_PATTERN.fullmatch(request_id) is None:
            request_id = uuid.uuid4().hex[:12]

        token = _request_id_var.set(request_id)
        logger = logging.getLogger("bookferry.bot")
        user = _event_user(event, data)
        kind = _update_kind(event)
        command = _command(event)
        callback_data = (
            event.callback_query.data
            if event.callback_query
            else None
        )
        started = time.perf_counter()

        log_event(
            logger,
            "UPDATE",
            user=user,
            update_id=event.update_id,
            type=kind,
            command=command,
            callback=callback_data,
        )

        try:
            result = await handler(event, data)
        except Exception:
            elapsed_ms = (time.perf_counter() - started) * 1000
            logger.exception(
                "request_id=%s UPDATE_ERROR telegram_id=%s type=%s "
                "duration_ms=%.1f",
                current_request_id(),
                user.id if user else "-",
                kind,
                elapsed_ms,
            )
            raise
        else:
            elapsed_ms = (time.perf_counter() - started) * 1000
            log_event(
                logger,
                "UPDATE_RESULT",
                user=user,
                type=kind,
                duration_ms=round(elapsed_ms, 1),
                result="handled",
            )
            return result
        finally:
            _request_id_var.reset(token)
