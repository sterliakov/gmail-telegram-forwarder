#! /usr/bin/env python

from __future__ import annotations

import logging
import pprint
from concurrent.futures import ThreadPoolExecutor, as_completed
from email.utils import parsedate_to_datetime

from googleapiclient.discovery import build

from . import config

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)


def read_emails(creds):
    query = "is:unread newer_than:1d"
    service = build("gmail", "v1", credentials=creds)
    results = (
        service.users().messages().list(userId="me", q=query, maxResults=100).execute()
    )
    messages = results.get("messages", [])
    try:
        known = set(config.KNOWN_IDS_FILE.read_text().splitlines())
    except FileNotFoundError:
        known = set()

    with ThreadPoolExecutor() as pool:
        jobs = {
            pool.submit(_retrieve_message, message["id"], creds): message["id"]
            for message in messages
        }
        for future in as_completed(jobs):
            try:
                result = future.result()
            except Exception:
                LOGGER.exception("Failed to retrieve message %s", jobs[future])
            else:
                parsed = _parse_message(result)
                if _is_new(parsed, known):
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
        "date": parsedate_to_datetime(headers["Date"]),
        "id": msg["id"],
    }


def _is_new(parsed_message, known):
    return parsed_message["id"] not in known


if __name__ == "__main__":
    for email in read_emails():
        pprint.pprint(email)  # noqa: T203  # Console code
