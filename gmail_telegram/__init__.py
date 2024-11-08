from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from .api import app
from .gmail_auth import GmailNotConfiguredError, GmailRefreshError, get_credentials
from .gmail_read import read_emails
from .storage import User, remember_ids
from .telegram import create_webhook, send_message, send_message_about_email

logging.basicConfig()
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)

__all__ = ["app", "create_webhook", "transmit_all_to_telegram"]


def transmit_all_to_telegram() -> None:
    for user in User.scan():
        transmit_to_telegram(user)


def transmit_to_telegram(user: User) -> None:
    try:
        get_credentials(user)
    except GmailNotConfiguredError:
        LOGGER.warning("Gmail not configured yet")
        return
    except GmailRefreshError:
        send_message(
            "Your Google token has expired. Send me /start to sign in again.",
            user.chat_id,
        )
        return

    notified = set()
    with ThreadPoolExecutor() as pool:
        jobs = {
            pool.submit(send_message_about_email, email, user): email["id"]
            for email in read_emails(user)
        }
        if not jobs:
            LOGGER.info("No new messages.")

        for future in as_completed(jobs):
            id_ = jobs[future]
            try:
                future.result()
            except Exception:
                LOGGER.exception(
                    "Failed to broadcast telegram message for email %s", id_
                )
            else:
                LOGGER.info("Successfully notified about email %s.", id_)
                notified.add(id_)

    remember_ids(notified, user)
