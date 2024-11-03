from __future__ import annotations

import os
from pathlib import Path

APP_ROOT = Path(__file__).parent.parent.resolve()

# FIXME: these should all go to secrets manager
TELEGRAM_AUTH_TOKEN = "FIXME"  # noqa: S105
GOOGLE_APP_CREDS_FILE = APP_ROOT / "app_credentials.json"

BOT_SECRET = os.getenv("BOT_SECRET")
if BOT_SECRET is None:
    raise RuntimeError("Bot secret must be set")

HOST = os.getenv("HOST")
if HOST is None:
    raise RuntimeError("Host must be set")

GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
