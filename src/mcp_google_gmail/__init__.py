from __future__ import annotations

import base64
import json
import os
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from mcp.server.fastmcp import FastMCP, Context

from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from services.gmail.app.google_gmail import (
    get_message as _get_message_impl,
    list_messages as _list_messages_impl,
    send_message as _send_message_impl,
    reply_to_message as _reply_impl,
    forward_message as _forward_impl,
    get_attachment as _get_attachment_impl,
    list_labels as _list_labels_impl,
    create_label as _create_label_impl,
    update_label as _update_label_impl,
    delete_label as _delete_label_impl,
    get_thread as _get_thread_impl,
    list_threads as _list_threads_impl,
    batch_modify_messages as _batch_modify_impl,
    batch_delete_messages as _batch_delete_impl,
)

SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.compose",
]
CREDENTIALS_CONFIG = os.environ.get("CREDENTIALS_CONFIG")
TOKEN_PATH = os.environ.get("TOKEN_PATH", "token.json")
CREDENTIALS_PATH = os.environ.get("CREDENTIALS_PATH", "credentials.json")
SERVICE_ACCOUNT_PATH = os.environ.get("SERVICE_ACCOUNT_PATH", "service_account.json")


@dataclass
class GmailContext:
    gmail_service: Any


@asynccontextmanager
async def gmail_lifespan(server: FastMCP) -> AsyncIterator[GmailContext]:
    creds = None
    if CREDENTIALS_CONFIG:
        creds = service_account.Credentials.from_service_account_info(
            json.loads(base64.b64decode(CREDENTIALS_CONFIG)), SCOPES)

    if SERVICE_ACCOUNT_PATH and os.path.exists(SERVICE_ACCOUNT_PATH):
        try:
            creds = service_account.Credentials.from_service_account_file(
                SERVICE_ACCOUNT_PATH, scopes=SCOPES)
            print("Using service account authentication (Gmail)")
        except Exception as e:
            print(f"Service account auth failed: {e}")
            creds = None

    if not creds:
        if os.path.exists(TOKEN_PATH):
            with open(TOKEN_PATH, "r") as token_file:
                creds = Credentials.from_authorized_user_info(json.load(token_file), SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
                creds = flow.run_local_server(port=0)
            with open(TOKEN_PATH, "w") as token_file:
                token_file.write(creds.to_json())

    gmail_service = build("gmail", "v1", credentials=creds)
    try:
        yield GmailContext(gmail_service=gmail_service)
    finally:
        pass


mcp = FastMCP(
    "Google Gmail",
    dependencies=["google-auth", "google-auth-oauthlib", "google-api-python-client"],
    lifespan=gmail_lifespan,
)


@mcp.tool()
def gmail_get_message(message_id: str, format: str = "full", ctx: Context = None) -> Dict[str, Any]:
    return _get_message_impl(message_id=message_id, format=format)


@mcp.tool()
def gmail_list_messages(query: Optional[str] = None, label_ids: Optional[List[str]] = None, include_spam_trash: bool = False, page_size: int = 20, page_token: Optional[str] = None, ctx: Context = None) -> Dict[str, Any]:
    return _list_messages_impl(query=query, label_ids=label_ids, include_spam_trash=include_spam_trash, page_size=page_size, page_token=page_token)


@mcp.tool()
def gmail_send_message(to: List[str], subject: str, body: str, cc: Optional[List[str]] = None, bcc: Optional[List[str]] = None, is_html: bool = False, attachments: Optional[List[Dict[str, Any]]] = None, ctx: Context = None) -> Dict[str, Any]:
    return _send_message_impl(to=to, subject=subject, body=body, cc=cc, bcc=bcc, is_html=is_html, attachments=attachments)


@mcp.tool()
def gmail_reply(message_id: str, body: str, is_html: bool = False, attachments: Optional[List[Dict[str, Any]]] = None, ctx: Context = None) -> Dict[str, Any]:
    return _reply_impl(message_id=message_id, body=body, is_html=is_html, attachments=attachments)


@mcp.tool()
def gmail_forward(message_id: str, to: List[str], body: Optional[str] = None, cc: Optional[List[str]] = None, bcc: Optional[List[str]] = None, is_html: bool = False, ctx: Context = None) -> Dict[str, Any]:
    return _forward_impl(message_id=message_id, to=to, body=body, cc=cc, bcc=bcc, is_html=is_html)


@mcp.tool()
def gmail_get_attachment(message_id: str, attachment_id: str, ctx: Context = None) -> Dict[str, Any]:
    return _get_attachment_impl(message_id=message_id, attachment_id=attachment_id)


@mcp.tool()
def gmail_list_labels(ctx: Context = None) -> Dict[str, Any]:
    return _list_labels_impl()


@mcp.tool()
def gmail_create_label(name: str, message_list_visibility: str = "show", label_list_visibility: str = "labelShow", color: Optional[Dict[str, Any]] = None, ctx: Context = None) -> Dict[str, Any]:
    return _create_label_impl(name=name, message_list_visibility=message_list_visibility, label_list_visibility=label_list_visibility, color=color)


@mcp.tool()
def gmail_update_label(label_id: str, name: Optional[str] = None, message_list_visibility: Optional[str] = None, label_list_visibility: Optional[str] = None, color: Optional[Dict[str, Any]] = None, ctx: Context = None) -> Dict[str, Any]:
    return _update_label_impl(label_id=label_id, name=name, message_list_visibility=message_list_visibility, label_list_visibility=label_list_visibility, color=color)


@mcp.tool()
def gmail_delete_label(label_id: str, ctx: Context = None) -> Dict[str, Any]:
    return _delete_label_impl(label_id=label_id)


@mcp.tool()
def gmail_get_thread(thread_id: str, format: str = "full", ctx: Context = None) -> Dict[str, Any]:
    return _get_thread_impl(thread_id=thread_id, format=format)


@mcp.tool()
def gmail_list_threads(query: Optional[str] = None, label_ids: Optional[List[str]] = None, include_spam_trash: bool = False, page_size: int = 20, page_token: Optional[str] = None, ctx: Context = None) -> Dict[str, Any]:
    return _list_threads_impl(query=query, label_ids=label_ids, include_spam_trash=include_spam_trash, page_size=page_size, page_token=page_token)


@mcp.tool()
def gmail_batch_modify(message_ids: List[str], add_label_ids: Optional[List[str]] = None, remove_label_ids: Optional[List[str]] = None, ctx: Context = None) -> Dict[str, Any]:
    return _batch_modify_impl(message_ids=message_ids, add_label_ids=add_label_ids, remove_label_ids=remove_label_ids)


@mcp.tool()
def gmail_batch_delete(message_ids: List[str], ctx: Context = None) -> Dict[str, Any]:
    return _batch_delete_impl(message_ids=message_ids)


def main():
    mcp.run()


if __name__ == "__main__":
    main() 