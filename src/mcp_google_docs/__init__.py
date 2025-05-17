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

from services.docs.app.google_docs import (
    create_document as _create_doc_impl,
    get_document as _get_doc_impl,
    list_documents as _list_docs_impl,
    get_document_content as _get_content_impl,
    insert_text as _insert_text_impl,
    replace_text as _replace_text_impl,
    format_text as _format_text_impl,
    append_paragraph as _append_para_impl,
    batch_update as _batch_update_impl,
    share_document as _share_doc_impl,
)

SCOPES = ["https://www.googleapis.com/auth/documents", "https://www.googleapis.com/auth/drive"]
CREDENTIALS_CONFIG = os.environ.get("CREDENTIALS_CONFIG")
TOKEN_PATH = os.environ.get("TOKEN_PATH", "token.json")
CREDENTIALS_PATH = os.environ.get("CREDENTIALS_PATH", "credentials.json")
SERVICE_ACCOUNT_PATH = os.environ.get("SERVICE_ACCOUNT_PATH", "service_account.json")
DRIVE_FOLDER_ID = os.environ.get("DRIVE_FOLDER_ID")


@dataclass
class DocsContext:
    docs_service: Any
    drive_service: Any
    folder_id: Optional[str] = None


@asynccontextmanager
async def docs_lifespan(server: FastMCP) -> AsyncIterator[DocsContext]:
    creds = None
    if CREDENTIALS_CONFIG:
        creds = service_account.Credentials.from_service_account_info(json.loads(base64.b64decode(CREDENTIALS_CONFIG)), SCOPES)

    if SERVICE_ACCOUNT_PATH and os.path.exists(SERVICE_ACCOUNT_PATH):
        try:
            creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_PATH, scopes=SCOPES)
            print("Using service account auth (Docs)")
        except Exception as e:
            print(f"Service account auth failed: {e}")
            creds = None

    if not creds:
        if os.path.exists(TOKEN_PATH):
            with open(TOKEN_PATH, "r") as tf:
                creds = Credentials.from_authorized_user_info(json.load(tf), SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
                creds = flow.run_local_server(port=0)
            with open(TOKEN_PATH, "w") as tf:
                tf.write(creds.to_json())

    docs_service = build("docs", "v1", credentials=creds)
    drive_service = build("drive", "v3", credentials=creds)
    try:
        yield DocsContext(docs_service=docs_service, drive_service=drive_service, folder_id=DRIVE_FOLDER_ID)
    finally:
        pass


mcp = FastMCP(
    "Google Docs",
    dependencies=["google-auth", "google-auth-oauthlib", "google-api-python-client"],
    lifespan=docs_lifespan,
)

# Tools
@mcp.tool()
def docs_create(title: str, content: Optional[str] = None, ctx: Context = None) -> Dict[str, Any]:
    folder_id = ctx.request_context.lifespan_context.folder_id if ctx else None
    return _create_doc_impl(title=title, content=content, folder_id=folder_id)

@mcp.tool()
def docs_get(document_id: str, ctx: Context = None) -> Dict[str, Any]:
    return _get_doc_impl(document_id=document_id)

@mcp.tool()
def docs_list(query: Optional[str] = None, page_size: int = 20, page_token: Optional[str] = None, order_by: Optional[str] = None, ctx: Context = None) -> Dict[str, Any]:
    return _list_docs_impl(query=query, page_size=page_size, page_token=page_token, order_by=order_by)

@mcp.tool()
def docs_get_content(document_id: str, mime_type: str = "text/plain", ctx: Context = None) -> Dict[str, Any]:
    return _get_content_impl(document_id=document_id, mime_type=mime_type)

@mcp.tool()
def docs_insert_text(document_id: str, text: str, index: int, ctx: Context = None) -> Dict[str, Any]:
    return _insert_text_impl(document_id=document_id, text=text, index=index)

@mcp.tool()
def docs_replace_text(document_id: str, text: str, start_index: int, end_index: int, ctx: Context = None) -> Dict[str, Any]:
    return _replace_text_impl(document_id=document_id, text=text, start_index=start_index, end_index=end_index)

@mcp.tool()
def docs_format_text(document_id: str, start_index: int, end_index: int, style: Dict[str, Any], ctx: Context = None) -> Dict[str, Any]:
    return _format_text_impl(document_id=document_id, start_index=start_index, end_index=end_index, style=style)

@mcp.tool()
def docs_append_paragraph(document_id: str, text: str, style: Optional[Dict[str, Any]] = None, ctx: Context = None) -> Dict[str, Any]:
    return _append_para_impl(document_id=document_id, text=text, style=style)

@mcp.tool()
def docs_batch_update(document_id: str, requests: List[Dict[str, Any]], ctx: Context = None) -> Dict[str, Any]:
    return _batch_update_impl(document_id=document_id, requests=requests)

@mcp.tool()
def docs_share(document_id: str, recipients: List[Dict[str, str]], send_notification: bool = False, ctx: Context = None) -> Dict[str, Any]:
    return _share_doc_impl(document_id=document_id, permissions=recipients, send_notification=send_notification)


def main():
    mcp.run()


if __name__ == "__main__":
    main() 