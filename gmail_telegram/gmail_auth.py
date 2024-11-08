from __future__ import annotations

import json
import logging
from urllib.parse import urljoin

from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow

from . import config
from .storage import User

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)

GOOGLE_REDIRECT_URI = urljoin(config.HOST, "/google-oauth/")


class GmailNotConfiguredError(Exception):
    """OAuth flow hasn't been completed yet."""


class GmailRefreshError(Exception):
    """OAuth flow hasn't been completed yet."""


def request_new_credentials(user: User) -> str:
    flow = _create_flow(user)
    uri, _ = flow.authorization_url(access_type="offline", prompt="consent")
    LOGGER.info("OAuth URL: %s", uri)
    return uri


def handle_oauth_callback(code: str, state: str) -> User:
    user = User.get(state)
    flow = _create_flow(user)
    flow.fetch_token(code=code)

    # Save the credentials for the next run
    user.gmail_auth = json.loads(flow.credentials.to_json())
    user.save()
    return user


def _create_flow(user: User) -> Flow:
    return Flow.from_client_config(
        config.GOOGLE_APP_CREDS,
        scopes=config.GMAIL_SCOPES,
        redirect_uri=GOOGLE_REDIRECT_URI,
        state=user.chat_id,
    )


def get_credentials(user: User) -> Credentials:
    creds = None
    if user.gmail_auth:
        creds = Credentials.from_authorized_user_info(
            user.gmail_auth, config.GMAIL_SCOPES
        )
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            LOGGER.info("Refreshing google credentials...")
            try:
                creds.refresh(Request())
            except RefreshError as exc:
                LOGGER.warning("Credentials expired forever.")
                raise GmailRefreshError from exc
            else:
                LOGGER.info("Credentials refreshed.")
                user.gmail_auth = json.loads(creds.to_json())
                user.save()
        else:
            raise GmailNotConfiguredError

    return creds
