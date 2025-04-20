#! /usr/bin/env python

from __future__ import annotations

import logging
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import TYPE_CHECKING, Any, TypeAlias, TypedDict

from googleapiclient.discovery import build

from .gmail_auth import get_credentials
from .storage import User, get_recent_known_ids

if TYPE_CHECKING:
    from google.oauth2.credentials import Credentials

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)

RawMessage: TypeAlias = Any


class MessageInfo(TypedDict):
    id: str
    subject: str
    from_: str
    snippet: str
    date: datetime


def read_emails(user: User) -> Iterator[MessageInfo]:
    creds = get_credentials(user)
    query = "is:unread newer_than:1d"
    service = build("gmail", "v1", credentials=creds)
    results = (
        service.users().messages().list(userId="me", q=query, maxResults=100).execute()
    )
    messages = results.get("messages", [])
    known = get_recent_known_ids(user.chat_id)

    with ThreadPoolExecutor() as pool:
        jobs = {
            pool.submit(_retrieve_message, message["id"], creds): message["id"]
            for message in messages
            if message["id"] not in known
        }
        for future in as_completed(jobs):
            try:
                result = future.result()
            except Exception:
                LOGGER.exception("Failed to retrieve message %s", jobs[future])
            else:
                yield _parse_message(result)


def _retrieve_message(message_id: str, creds: Credentials) -> RawMessage:
    service = build("gmail", "v1", credentials=creds)
    return service.users().messages().get(userId="me", id=message_id).execute()


def _parse_message(msg: RawMessage) -> MessageInfo:
    # This conversion is not guaranteed to be loseless (=name may be not unique?),
    # but we know that headers of interest are unique.
    headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
    return {
        "subject": headers.get("Subject", "<No subject>"),
        "from_": headers["From"],
        "snippet": msg["snippet"],
        "date": parsedate_to_datetime(headers["Date"]),
        "id": msg["id"],
    }
