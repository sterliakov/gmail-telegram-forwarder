#! /usr/bin/env python
from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from filelock import FileLock

from gmail_telegram import config
from gmail_telegram.gmail_auth import (
    GmailNotConfiguredError,
    GmailRefreshError,
    get_credentials,
)
from gmail_telegram.gmail_read import read_emails
from gmail_telegram.telegram import (
    greet_user,
    handle_telegram_starts,
    send_message,
    send_message_about_email,
)

logging.basicConfig()
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)


def transmit_all_to_telegram():
    can_forward = handle_telegram_starts()
    if not can_forward:
        LOGGER.warning("No destination set yet, skipping.")
        return

    try:
        creds = get_credentials()
    except GmailNotConfiguredError:
        LOGGER.warning("Gmail not configured yet")
        return
    except GmailRefreshError:
        send_message("Your Google token has expired.")
        greet_user(None)
        return

    notified = set()
    with ThreadPoolExecutor() as pool:
        jobs = {
            pool.submit(send_message_about_email, email): email["id"]
            for email in read_emails(creds)
        }
        if not jobs:
            LOGGER.info("No new messages.")

        for future in as_completed(jobs):
            id_ = jobs[future]
            try:
                future.result()
            except Exception:
                LOGGER.exception(
                    "Failed to broadcast telegram message for email %s",
                    id_,
                )
            else:
                LOGGER.info("Successfully notified about email %s.", id_)
                notified.add(id_)

    with config.KNOWN_IDS_FILE.open("a") as log:
        for id_ in notified:
            log.write(f"{id_}\n")


if __name__ == "__main__":
    with FileLock(config.LOCK_FILE):
        transmit_all_to_telegram()
