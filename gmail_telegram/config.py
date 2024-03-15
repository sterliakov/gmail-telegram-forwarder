from __future__ import annotations

import os
from pathlib import Path

APP_ROOT = Path(__file__).parent.parent.resolve()
TEMP_FILES_ROOT = APP_ROOT / ".temp_files"

TEMP_FILES_ROOT.mkdir(exist_ok=True)
CHAT_ID_FILE = TEMP_FILES_ROOT / "chat_id"
LAST_VISIT_FILE = TEMP_FILES_ROOT / "last_visit"
LATEST_TG_UPDATE_FILE = TEMP_FILES_ROOT / "tg_polling"
LOCK_FILE = TEMP_FILES_ROOT / "lock"
GOOGLE_CREDS_FILE = TEMP_FILES_ROOT / "token.json"

GOOGLE_APP_CREDS_FILE = APP_ROOT / "app_credentials.json"

BOT_SECRET = os.getenv("BOT_SECRET")
if BOT_SECRET is None:
    raise RuntimeError("Bot secret must be set")

HOST = os.getenv("GOOGLE_AUTH_HOST")
if HOST is None:
    raise RuntimeError("Host must be set")

PORT = int(os.getenv("GOOGLE_OAUTH_PORT", "9090"))
