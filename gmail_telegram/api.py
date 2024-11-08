from __future__ import annotations

from pathlib import Path
from typing import Annotated, Any, Final

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from . import config
from .gmail_auth import handle_oauth_callback
from .telegram import handle_telegram_starts, send_message

app = FastAPI()
SUCCESS_HTML_FILE: Final = Path(__file__).parent / "data" / "success.html"


class TelegramMessage(BaseModel):
    message: Any = None
    my_chat_member: Any = None


@app.post("/tg-update/")
async def telegram_webhook(
    body: TelegramMessage,
    x_telegram_bot_api_secret_token: Annotated[str | None, Header()] = None,
) -> Any:
    token = x_telegram_bot_api_secret_token
    if token != config.TELEGRAM_AUTH_TOKEN:
        raise HTTPException(403, "Incorrect token")
    handle_telegram_starts(body.model_dump())
    return {"success": True}


@app.get("/google-oauth/", response_class=HTMLResponse)
async def google_callback(code: str, state: str) -> Any:
    user = handle_oauth_callback(code, state)
    send_message("You're all set!", user.chat_id)
    return HTMLResponse(SUCCESS_HTML_FILE.read_text())
