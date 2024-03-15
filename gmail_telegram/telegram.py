from __future__ import annotations

import contextlib
import logging
from urllib.parse import quote

import requests

from . import config
from .gmail_auth import request_new_credentials

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)

API_ROOT = f"https://api.telegram.org/bot{config.BOT_SECRET}"
MESSAGE_TEMPLATE = """
New email from {from}!

# {subject}

Short extract:
{snippet}
"""


def send_telegram_message(email):
    msg = MESSAGE_TEMPLATE.format(**email)
    _send_message(msg)


def handle_telegram_starts():
    already_connected = (
        config.CHAT_ID_FILE.exists() and config.GOOGLE_CREDS_FILE.exists()
    )
    api_url = f"{API_ROOT}/getUpdates"
    with contextlib.suppress(FileNotFoundError):
        api_url += "?offset=" + str(int(config.LATEST_TG_UPDATE_FILE.read_text()) + 1)
    response = requests.get(api_url, timeout=10)
    response.raise_for_status()
    data = response.json()
    if not data["ok"]:
        raise RuntimeError("Failed to retrieve telegram updates")
    result = data.get("result", [])
    max_update_id = max((r["update_id"] for r in result), default=0)
    config.LATEST_TG_UPDATE_FILE.write_text(str(max_update_id))
    result = [r for r in result if r["message"]["text"] == "/start"]
    chat_ids = {r["message"]["chat"]["id"] for r in result}
    if len(result) > 1:
        for chat_id in chat_ids:
            _send_message("Sorry, cannot connect now.", chat_id)
        raise RuntimeError("Got several messages. Only one account can be in use.")
    if result and already_connected:
        LOGGER.warning("Got a new message, but an account is already connected.")
        for chat_id in chat_ids:
            _send_message("Sorry, cannot connect now.", chat_id)
        return True
    if result:
        message = result[0]["message"]
        chat_id = message["chat"]["id"]
        config.CHAT_ID_FILE.write_text(str(chat_id))
        greet_user(chat_id)

    return config.GOOGLE_CREDS_FILE.exists()


def greet_user(chat_id):
    if config.GOOGLE_CREDS_FILE.exists():
        _send_message("Congrats! You're all set now.")
        return

    creds_state_machine = request_new_credentials()
    url = next(creds_state_machine)
    _send_message(f"Head to {url} to connect your GMail account.", chat_id)
    next(creds_state_machine)
    _send_message("Congrats! You're all set now.", chat_id)


def _as_url(message: str, chat_id=None) -> str:
    if chat_id is None:
        try:
            chat_id = config.CHAT_ID_FILE.read_text()
        except FileNotFoundError as exc:
            raise RuntimeError("Chat not set up yet.") from exc

    return f"{API_ROOT}/sendMessage?chat_id={chat_id}&text={quote(message, safe='')}"


def _send_message(text, chat_id=None):
    url = _as_url(text, chat_id)
    requests.post(url, timeout=10).raise_for_status()
    return {"result": "OK"}
