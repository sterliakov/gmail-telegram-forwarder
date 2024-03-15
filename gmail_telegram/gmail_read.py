#! /usr/bin/env python

from __future__ import annotations

import logging
import pprint
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime, timedelta
from email.utils import parsedate

from googleapiclient.discovery import build

from . import config
from .gmail_auth import get_credentials

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)


def read_emails():
    creds = get_credentials()

    query = "is:unread newer_than:1d"
    service = build("gmail", "v1", credentials=creds)
    results = (
        service.users()
        .messages()
        .list(userId="me", labelIds=["INBOX"], q=query, maxResults=100)
        .execute()
    )
    messages = results.get("messages", [])
    last_visit = _get_last_run_time()
    _write_last_run_time()

    with ThreadPoolExecutor() as pool:
        jobs = {
            pool.submit(_retrieve_message, message["id"], creds): message["id"]
            for message in messages
        }
        for future in as_completed(jobs):
            try:
                result = future.result()
            except Exception:
                LOGGER.exception("Failed to retrieve message %s", jobs["future"])
            else:
                parsed = _parse_message(result)
                if _is_new(parsed, last_visit):
                    yield parsed


def _retrieve_message(message_id, creds):
    service = build("gmail", "v1", credentials=creds)
    return service.users().messages().get(userId="me", id=message_id).execute()


def _parse_message(msg):
    # This conversion is not guaranted to be loseless (=name may be not unique?),
    # but we know that headers of interest are unique.
    headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
    return {
        "subject": headers.get("Subject", "<No subject>"),
        "from": headers["From"],
        "snippet": msg["snippet"],
        "date": datetime.fromtimestamp(time.mktime(parsedate(headers["Date"])), tz=UTC),
        "id": msg["id"],
    }


def _is_new(parsed_message, last_visit):
    return parsed_message["date"] >= last_visit


def _get_last_run_time():
    try:
        timestamp = config.LAST_VISIT_FILE.stat().st_mtime
    except FileNotFoundError:
        return datetime.now(tz=UTC) - timedelta(days=1)
    else:
        return datetime.fromtimestamp(timestamp, tz=UTC)


def _write_last_run_time():
    config.LAST_VISIT_FILE.touch()


if __name__ == "__main__":
    for email in read_emails():
        pprint.pprint(email)  # noqa: T203  # Console code
