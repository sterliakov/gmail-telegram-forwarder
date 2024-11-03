from __future__ import annotations

import logging
from typing import Any
from urllib.parse import quote, urljoin

import requests

from . import config
from .gmail_auth import request_new_credentials
from .storage import User

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)

API_ROOT = f"https://api.telegram.org/bot{config.BOT_SECRET}"
MESSAGE_TEMPLATE = """
New email from {from}!

# {subject}

Short extract:
{snippet}
"""


def send_message_about_email(email: dict[str, Any], user: User) -> None:
    msg = MESSAGE_TEMPLATE.format(**email)
    send_message(msg, user.chat_id)


def handle_telegram_starts(event) -> None:
    LOGGER.info("Message: %s", event)
    match event:
        case {"message": {"from": {"id": chat_id}, "text": text}}:
            if text.strip() != "/start":
                send_message("Unknown command: I only understand /start.", chat_id)
                return
            user = active_user_for_chat(chat_id)
            if user is None:
                user = User(chat_id)
                user.save()
                url = request_new_credentials(user)
                send_message(f"Head to {url} to connect your GMail account.", chat_id)
            else:
                send_message("Already connected!", chat_id)
        case {"message": {"from": {"id": chat_id}}}:
            send_message("Unknown command: I only understand /start.", chat_id)
            return


def active_user_for_chat(chat_id: str) -> User | None:
    try:
        user = User.get(chat_id)
        if user.gmail_auth is None:
            return None
    except User.DoesNotExist:
        return None
    else:
        return user


def _as_url(message: str, chat_id: str) -> str:
    return f"{API_ROOT}/sendMessage?chat_id={chat_id}&text={quote(message, safe='')}"


def send_message(text: str, chat_id: str) -> None:
    url = _as_url(text, chat_id)
    requests.post(url, timeout=10).raise_for_status()


def create_webhook() -> None:
    response = requests.post(
        f"{API_ROOT}/setWebhook",
        params={
            "url": urljoin(config.HOST, "/tg-update/"),
            "allowed_updates": ["message"],
            "max_connections": 1,
            "secret_token": config.TELEGRAM_AUTH_TOKEN,
        },
        timeout=10,
    )
    response.raise_for_status()
