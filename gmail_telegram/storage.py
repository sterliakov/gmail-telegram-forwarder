from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime, timedelta

from pynamodb.attributes import (
    JSONAttribute,
    NumberAttribute,
    TTLAttribute,
    UnicodeAttribute,
    UnicodeSetAttribute,
)
from pynamodb.models import Model


class User(Model):
    class Meta:
        table_name = "users"
        host = "http://localhost:8181"

    chat_id = UnicodeAttribute(hash_key=True)
    last_update = NumberAttribute(null=True)
    gmail_auth = JSONAttribute(null=True)


class TransmittedMessages(Model):
    class Meta:
        table_name = "messages"
        host = "http://localhost:8181"

    day = UnicodeAttribute(null=True, hash_key=True)
    chat_id = UnicodeAttribute(range_key=True)
    ttl = TTLAttribute(default=timedelta(days=7))
    email_ids = UnicodeSetAttribute(attr_name="ids")


def get_recent_known_ids(user_id: str) -> set[str]:
    now = datetime.now(tz=UTC)
    yesterday = now - timedelta(hours=24)
    messages = TransmittedMessages.batch_get([
        (now.date().isoformat(), user_id),
        (yesterday.date().isoformat(), user_id),
    ])
    ids = set()
    for message in messages:
        ids |= message.email_ids
    return ids


def remember_ids(ids: Iterable[str], user: User) -> None:
    ids = list(ids)
    if not ids:
        return
    now = datetime.now(tz=UTC)
    curr = TransmittedMessages(now.date().isoformat(), user.chat_id)
    curr.update(actions=[TransmittedMessages.email_ids.add(*ids)])
