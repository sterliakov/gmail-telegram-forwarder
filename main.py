#! /usr/bin/env python
from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from urllib.parse import urlparse

from mangum import Mangum

from gmail_telegram import app, create_webhook, transmit_all_to_telegram

if TYPE_CHECKING:
    from mangum.types import LambdaContext, LambdaEvent

logging.basicConfig()
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)


class MangumExtended(Mangum):
    def _patch_event_path(self, event: LambdaEvent) -> None:
        real_path = event["rawPath"]
        split_path = event["requestContext"]["http"]["path"]
        # Lambda Function URL decides to remove trailing slash for some reason.
        if urlparse(real_path).path.endswith("/") and not split_path.endswith("/"):
            event["requestContext"]["http"]["path"] += "/"

    def __call__(self, event: LambdaEvent, context: LambdaContext) -> dict[str, object]:
        action = event.get("action")
        if action == "CHECK":
            transmit_all_to_telegram()
            return {"success": True}
        if action == "CREATE_WEBHOOK":
            create_webhook()
            return {"success": True}
        if action is not None:
            raise ValueError(f"Unknown action: {action}.")

        self._patch_event_path(event)
        return super().__call__(event, context)


handler = MangumExtended(app, lifespan="off")
