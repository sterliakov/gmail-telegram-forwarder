#! /usr/bin/env python
from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from filelock import FileLock

from gmail_telegram import config
from gmail_telegram.gmail_read import read_emails
from gmail_telegram.telegram import handle_telegram_starts, send_telegram_message

logging.basicConfig()
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)


def transmit_all_to_telegram():
    can_forward = handle_telegram_starts()
    if not can_forward:
        LOGGER.warning("No destination set yet, skipping.")
        return

    with ThreadPoolExecutor() as pool:
        jobs = {
            pool.submit(send_telegram_message, email): email["id"]
            for email in read_emails()
        }
        if not jobs:
            LOGGER.info("No new messages.")

        for future in as_completed(jobs):
            try:
                future.result()
            except Exception:
                LOGGER.exception(
                    "Failed to broadcast telegram message for email %s",
                    jobs[future],
                )
            else:
                LOGGER.info("Successfully notified about email %s.", jobs[future])


if __name__ == "__main__":
    with FileLock(config.LOCK_FILE):
        transmit_all_to_telegram()
