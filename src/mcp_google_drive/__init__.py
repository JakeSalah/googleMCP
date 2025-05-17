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

from services.drive.app.google_drive import (
    search_files as _search_files_impl,
    create_folder as _create_folder_impl,
    upload_file as _upload_file_impl,
    move_file as _move_file_impl,
    rename_file as _rename_file_impl,
    delete_file as _delete_file_impl,
    get_file_content as _get_file_content_impl,
    share_file as _share_file_impl,
    get_file_metadata as _get_file_metadata_impl,
)

SCOPES = ["https://www.googleapis.com/auth/drive"]
CREDENTIALS_CONFIG = os.environ.get("CREDENTIALS_CONFIG")
TOKEN_PATH = os.environ.get("TOKEN_PATH", "token.json")
CREDENTIALS_PATH = os.environ.get("CREDENTIALS_PATH", "credentials.json")
SERVICE_ACCOUNT_PATH = os.environ.get("SERVICE_ACCOUNT_PATH", "service_account.json")


@dataclass
class DriveContext:
    drive_service: Any


@asynccontextmanager
async def drive_lifespan(server: FastMCP) -> AsyncIterator[DriveContext]:
    creds = None
    if CREDENTIALS_CONFIG:
        creds = service_account.Credentials.from_service_account_info(
            json.loads(base64.b64decode(CREDENTIALS_CONFIG)), SCOPES)

    if SERVICE_ACCOUNT_PATH and os.path.exists(SERVICE_ACCOUNT_PATH):
        try:
            creds = service_account.Credentials.from_service_account_file(
                SERVICE_ACCOUNT_PATH, scopes=SCOPES)
            print("Using service account authentication (Drive)")
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

    drive_service = build("drive", "v3", credentials=creds)
    try:
        yield DriveContext(drive_service=drive_service)
    finally:
        pass


mcp = FastMCP(
    "Google Drive",
    dependencies=["google-auth", "google-auth-oauthlib", "google-api-python-client"],
    lifespan=drive_lifespan,
)


@mcp.tool()
def search_files(query: str, page_size: int = 100, page_token: Optional[str] = None, order_by: Optional[str] = None, ctx: Context = None) -> Dict[str, Any]:
    return _search_files_impl(q=query, page_size=page_size, page_token=page_token, order_by=order_by)


@mcp.tool()
def create_folder(name: str, parent_id: Optional[str] = None, ctx: Context = None) -> Dict[str, Any]:
    return _create_folder_impl(name=name, parent_id=parent_id)


@mcp.tool()
def upload_file(name: str, mime_type: str, content_base64: str, parent_id: Optional[str] = None, ctx: Context = None) -> Dict[str, Any]:
    return _upload_file_impl(name=name, mime_type=mime_type, content_base64=content_base64, parent_id=parent_id)


@mcp.tool()
def move_file(file_id: str, new_parent_id: str, ctx: Context = None) -> Dict[str, Any]:
    return _move_file_impl(file_id=file_id, new_parent_id=new_parent_id)


@mcp.tool()
def rename_file(file_id: str, new_name: str, ctx: Context = None) -> Dict[str, Any]:
    return _rename_file_impl(file_id=file_id, new_name=new_name)


@mcp.tool()
def delete_file(file_id: str, ctx: Context = None) -> Dict[str, Any]:
    return _delete_file_impl(file_id=file_id)


@mcp.tool()
def get_file_content(file_id: str, ctx: Context = None) -> Dict[str, Any]:
    return _get_file_content_impl(file_id=file_id)


@mcp.tool()
def share_file(file_id: str, recipients: List[Dict[str, str]], send_notification: bool = False, ctx: Context = None) -> Dict[str, Any]:
    return _share_file_impl(file_id=file_id, permissions=recipients, send_notification=send_notification)


@mcp.tool()
def get_file_metadata(file_id: str, ctx: Context = None) -> Dict[str, Any]:
    return _get_file_metadata_impl(file_id=file_id)


def main():  # pragma: no cover
    mcp.run()


if __name__ == "__main__":
    main() 