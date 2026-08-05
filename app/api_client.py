from email.message import Message as EmailMessage

import httpx
from app.config import settings


class BookFerryApiError(Exception):
    pass


async def get_telegram_user(
    telegram_id: int,
) -> dict | None:
    url = (
        f"{settings.api_base_url}"
        f"/users/telegram/{telegram_id}"
    )

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
    except httpx.RequestError as error:
        raise BookFerryApiError(
            "Не удалось подключиться к серверу"
        ) from error

    if response.status_code == 404:
        return None

    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as error:
        raise BookFerryApiError(
            f"Сервер вернул ошибку {response.status_code}"
        ) from error

    return response.json()


async def update_opds(
    telegram_id: int,
    opds_url: str,
) -> None:
    await _patch_user_setting(
        telegram_id=telegram_id,
        setting="opds",
        payload={
            "opds_url": opds_url,
        },
    )


async def update_emails(
    telegram_id: int,
    emails: str,
) -> None:
    await _patch_user_setting(
        telegram_id=telegram_id,
        setting="emails",
        payload={
            "emails": emails,
        },
    )


async def update_subject(
    telegram_id: int,
    subject: str | None,
) -> None:
    await _patch_user_setting(
        telegram_id=telegram_id,
        setting="subject",
        payload={
            "subject": subject,
        },
    )


async def _patch_user_setting(
    telegram_id: int,
    setting: str,
    payload: dict,
) -> None:
    url = (
        f"{settings.api_base_url}"
        f"/users/telegram/{telegram_id}/{setting}"
    )

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.patch(
                url,
                json=payload,
            )
    except httpx.RequestError as error:
        raise BookFerryApiError(
            "Не удалось подключиться к серверу"
        ) from error

    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as error:
        raise BookFerryApiError(
            f"Сервер вернул ошибку {response.status_code}: "
            f"{response.text}"
        ) from error
from email.message import Message as EmailMessage

import httpx

from app.config import settings


class BookFerryApiError(Exception):
    pass

async def search_books(
    telegram_id: int,
    query: str,
) -> list[dict]:
    async with httpx.AsyncClient(timeout=180) as client:
        try:
            response = await client.post(
                f"{settings.api_base_url}/search",
                json={
                    "telegram_id": telegram_id,
                    "query": query,
                },
            )
        except httpx.RequestError as error:
            raise BookFerryApiError(
                "Сервер BookFerry недоступен"
            ) from error

    if response.status_code == 404:
        raise BookFerryApiError(
            "Сначала выполните настройку: /setting"
        )

    if response.is_error:
        raise BookFerryApiError(
            f"Ошибка поиска: {response.status_code}\n"
            f"{response.text}"
        )

    return response.json()


async def download_book(
    telegram_id: int,
    url: str,
) -> tuple[bytes, str]:
    timeout = httpx.Timeout(
        120,
        connect=10,
    )

    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            response = await client.post(
                f"{settings.api_base_url}/send-book",
                json={
                    "telegram_id": telegram_id,
                    "url": url,
                },
            )
        except httpx.RequestError as error:
            raise BookFerryApiError(
                "Сервер BookFerry недоступен"
            ) from error

    if response.is_error:
        raise BookFerryApiError(
            f"Ошибка скачивания: {response.status_code}\n"
            f"{response.text}"
        )

    content_disposition = response.headers.get(
        "content-disposition"
    )

    if not content_disposition:
        raise BookFerryApiError(
            "Сервер не вернул имя файла"
        )

    header = EmailMessage()
    header["content-disposition"] = content_disposition

    filename = header.get_filename()

    if not filename:
        raise BookFerryApiError(
            "Не удалось прочитать имя файла"
        )

    return response.content, filename
