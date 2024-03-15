from __future__ import annotations

import logging
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow

from . import config

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


class GmailNotConfiguredError(Exception):
    """OAuth flow hasn't been completed yet."""


def request_new_credentials(port=config.PORT):
    flow = Flow.from_client_secrets_file(
        config.GOOGLE_APP_CREDS_FILE,
        SCOPES,
        redirect_uri=config.HOST,
    )
    uri, _ = flow.authorization_url(access_type="offline")
    LOGGER.info("OAuth URL: %s", uri)
    yield uri
    handler_cls, response = _make_handler_cls()
    server = HTTPServer(("", port), handler_cls)
    server.timeout = 5 * 60
    server.handle_request()
    flow.fetch_token(code=response["code"])

    # Save the credentials for the next run
    with config.GOOGLE_CREDS_FILE.open("w") as token:
        token.write(flow.credentials.to_json())

    yield flow.credentials


def get_credentials():
    creds = None
    if config.GOOGLE_CREDS_FILE.exists():
        creds = Credentials.from_authorized_user_file(
            str(config.GOOGLE_CREDS_FILE.resolve()),
            SCOPES,
        )
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with config.GOOGLE_CREDS_FILE.open("w") as token:
                token.write(creds.to_json())
        else:
            raise GmailNotConfiguredError

    return creds


def _make_handler_cls():
    response = {}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            nonlocal response
            qs = urlparse(self.path).query
            parsed = parse_qs(qs)
            response |= {k: v[0] for k, v in parsed.items()}

            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"Success!")

    return Handler, response
