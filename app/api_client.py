from email.message import Message as EmailMessage

import httpx

from app.config import settings


class BookFerryApiError(Exception):
    pass


def _response_detail(response: httpx.Response) -> str:
    try:
        data = response.json()
    except ValueError:
        return response.text.strip() or f"HTTP {response.status_code}"

    if isinstance(data, dict) and data.get("detail"):
        return str(data["detail"])

    return response.text.strip() or f"HTTP {response.status_code}"


async def get_telegram_user(
    telegram_id: int,
) -> dict | None:
    url = (
        f"{settings.api_base_url}"
        f"/users/telegram/{telegram_id}"
    )

    try:
        async with httpx.AsyncClient(
            timeout=10.0
        ) as client:
            response = await client.get(url)
    except httpx.RequestError as error:
        raise BookFerryApiError(
            "Не удалось подключиться к серверу BookFerry"
        ) from error

    if response.status_code == 404:
        return None

    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as error:
        raise BookFerryApiError(
            f"Сервер вернул ошибку: {_response_detail(response)}"
        ) from error

    return response.json()


async def get_catalogs() -> list[dict]:
    try:
        async with httpx.AsyncClient(
            timeout=10.0
        ) as client:
            response = await client.get(
                f"{settings.api_base_url}/catalogs"
            )
    except httpx.RequestError as error:
        raise BookFerryApiError(
            "Не удалось подключиться к серверу BookFerry"
        ) from error

    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as error:
        raise BookFerryApiError(
            f"Не удалось получить список библиотек: "
            f"{_response_detail(response)}"
        ) from error

    data = response.json()

    if not isinstance(data, list):
        raise BookFerryApiError(
            "Сервер вернул некорректный список библиотек"
        )

    return data


async def update_catalog(
    telegram_id: int,
    catalog_id: int,
) -> dict:
    return await _patch_user_setting(
        telegram_id=telegram_id,
        setting="catalog",
        payload={
            "catalog_id": catalog_id,
        },
    )


async def update_opds(
    telegram_id: int,
    opds_url: str,
) -> dict:
    return await _patch_user_setting(
        telegram_id=telegram_id,
        setting="opds",
        payload={
            "opds_url": opds_url,
        },
    )


async def update_emails(
    telegram_id: int,
    emails: str,
) -> dict:
    return await _patch_user_setting(
        telegram_id=telegram_id,
        setting="emails",
        payload={
            "emails": emails,
        },
    )


async def update_subject(
    telegram_id: int,
    subject: str | None,
) -> dict:
    return await _patch_user_setting(
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
) -> dict:
    url = (
        f"{settings.api_base_url}"
        f"/users/telegram/{telegram_id}/{setting}"
    )

    try:
        async with httpx.AsyncClient(
            timeout=30.0
        ) as client:
            response = await client.patch(
                url,
                json=payload,
            )
    except httpx.RequestError as error:
        raise BookFerryApiError(
            "Не удалось подключиться к серверу BookFerry"
        ) from error

    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as error:
        raise BookFerryApiError(
            _response_detail(response)
        ) from error

    if not response.content:
        return {}

    return response.json()


async def search_books(
    telegram_id: int,
    query: str,
    page_url: str | None = None,
) -> dict:
    payload = {
        "telegram_id": telegram_id,
        "query": query,
    }

    if page_url:
        payload["page_url"] = page_url

    async with httpx.AsyncClient(
        timeout=180
    ) as client:
        try:
            response = await client.post(
                f"{settings.api_base_url}/search",
                json=payload,
            )
        except httpx.RequestError as error:
            raise BookFerryApiError(
                "Сервер BookFerry недоступен"
            ) from error

    if response.status_code == 404:
        raise BookFerryApiError(
            "Сначала откройте Menu → «Мастер настройки»."
        )

    if response.is_error:
        raise BookFerryApiError(
            f"Не удалось выполнить поиск: {_response_detail(response)}"
        )

    data = response.json()

    if isinstance(data, list):
        return {
            "books": data,
            "next_page_url": None,
        }

    return data


async def download_book(
    telegram_id: int,
    url: str,
) -> tuple[bytes, str]:
    timeout = httpx.Timeout(
        120,
        connect=10,
    )

    async with httpx.AsyncClient(
        timeout=timeout
    ) as client:
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
            f"Не удалось получить книгу: {_response_detail(response)}"
        )

    content_disposition = response.headers.get(
        "content-disposition"
    )

    if not content_disposition:
        raise BookFerryApiError(
            "Сервер не вернул имя файла"
        )

    header = EmailMessage()
    header["content-disposition"] = (
        content_disposition
    )

    filename = header.get_filename()

    if not filename:
        raise BookFerryApiError(
            "Не удалось определить имя файла"
        )

    return response.content, filename
