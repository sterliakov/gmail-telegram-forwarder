from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Final

import boto3

APP_ROOT = Path(__file__).parent.parent.resolve()


def _get_secret(secret_path: str) -> dict[str, Any]:
    secret_manager = boto3.client(service_name="secretsmanager")
    response = secret_manager.get_secret_value(SecretId=secret_path)
    return json.loads(response["SecretString"])


if os.getenv("DEBUG", "").lower() in {"true", "1"}:
    _secret: dict[str, Any] = {
        "telegram_auth_header": "temp",
        "google_credentials": (APP_ROOT / "app_credentials.json").read_text(),
        "bot_secret": os.getenv("BOT_SECRET"),
        "host": os.getenv("HOST"),
    }
    if _secret["bot_secret"] is None:
        raise RuntimeError("BOT_SECRET must me set")
    if _secret["host"] is None:
        raise RuntimeError("HOST must me set")
else:
    _secret_name = os.getenv("SECRET_NAME")
    if not _secret_name:
        raise RuntimeError("SECRET_NAME must be set")
    _secret = _get_secret(_secret_name)

TELEGRAM_AUTH_TOKEN: Final[str] = _secret["telegram_auth_header"]
GOOGLE_APP_CREDS: Final[dict[str, Any]] = json.loads(_secret["google_credentials"])
BOT_SECRET: Final[str] = _secret["bot_secret"]
HOST: Final[str] = _secret["host"]

GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
