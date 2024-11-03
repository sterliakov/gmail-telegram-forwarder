from __future__ import annotations

import logging
from typing import Annotated, Any

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

from gmail_telegram import config
from gmail_telegram.gmail_auth import handle_oauth_callback
from gmail_telegram.telegram import handle_telegram_starts

logging.basicConfig()
app = FastAPI()


class TelegramMessage(BaseModel):
    message: Any


@app.post("/tg-update/")
async def telegram_webhook(
    body: TelegramMessage,
    x_telegram_bot_api_secret_token: Annotated[str | None, Header()] = None,
):
    token = x_telegram_bot_api_secret_token
    if token != config.TELEGRAM_AUTH_TOKEN:
        raise HTTPException(403, "Incorrect token")
    handle_telegram_starts(body.dict())
    return {"success": True}


@app.get("/google-oauth/")
async def google_callback(code: str, state: str):
    handle_oauth_callback(code, state)
    return {"success": True}
