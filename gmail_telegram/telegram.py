from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any
from urllib.parse import quote, urljoin

import requests

from . import config
from .gmail_auth import request_new_credentials
from .storage import User

if TYPE_CHECKING:
    from .gmail_read import MessageInfo

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)

API_ROOT = f"https://api.telegram.org/bot{config.BOT_SECRET}"
MESSAGE_TEMPLATE = """
New email from {from_}!

# {subject}

Short extract:
{snippet}
"""


def send_message_about_email(email: MessageInfo, user: User) -> None:
    msg = MESSAGE_TEMPLATE.format(**email)
    send_message(msg, user.chat_id)


def handle_telegram_starts(event: dict[str, Any]) -> None:
    LOGGER.info("Message: %s", event)
    match event:
        case {"message": {"from": {"id": chat_id}, "text": text}}:
            chat_id = str(chat_id)
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
            chat_id = str(chat_id)
            send_message("Unknown command: I only understand /start.", chat_id)
            return
        case {
            "my_chat_member": {
                "chat": {"id": chat_id},
                "new_chat_member": {"status": "kicked"},
            }
        }:
            chat_id = str(chat_id)
            user = active_user_for_chat(chat_id)
            if user is None:
                LOGGER.warning("Requested disconnect for unknown chat %s", chat_id)
            else:
                LOGGER.info("Disconnecting %s...", chat_id)
                user.delete()
                LOGGER.info("Disconnected %s.", chat_id)


def active_user_for_chat(chat_id: str) -> User | None:
    try:
        user = User.get(chat_id)
        if user.gmail_auth is None:
            return None
    except User.DoesNotExist:
        return None
    else:
        return user


def _as_url(message: str, chat_id: str | int) -> str:
    return f"{API_ROOT}/sendMessage?chat_id={chat_id}&text={quote(message, safe='')}"


def send_message(text: str, chat_id: str | int) -> None:
    url = _as_url(text, chat_id)
    requests.post(url, timeout=10).raise_for_status()


def create_webhook() -> None:
    params: dict[str, Any] = {
        "url": urljoin(config.HOST, "/tg-update/"),
        "allowed_updates": ["message"],
        "max_connections": 1,
        "secret_token": config.TELEGRAM_AUTH_TOKEN,
    }
    response = requests.post(f"{API_ROOT}/setWebhook", params=params, timeout=10)
    response.raise_for_status()
