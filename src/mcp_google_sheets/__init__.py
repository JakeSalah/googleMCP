from __future__ import annotations
# NOTE: Initial skeleton for FastMCP Google Sheets server following upstream architecture
# TODO: integrate full set of tools from existing Google Sheets MCP

import base64
import json
import os
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

# FastMCP
from mcp.server.fastmcp import FastMCP, Context

# Google APIs
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Existing implementation
from services.sheets.app.google_sheets import (
    create_spreadsheet as _create_spreadsheet_impl,
    get_spreadsheet as _get_spreadsheet_impl,
    list_spreadsheets as _list_spreadsheets_impl,
    get_values as _get_values_impl,
    update_values as _update_values_impl,
    append_values as _append_values_impl,
    clear_values as _clear_values_impl,
    add_sheet as _add_sheet_impl,
    delete_sheet as _delete_sheet_impl,
    rename_sheet as _rename_sheet_impl,
    share_spreadsheet as _share_spreadsheet_impl,
)


SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
CREDENTIALS_CONFIG = os.environ.get('CREDENTIALS_CONFIG')
TOKEN_PATH = os.environ.get('TOKEN_PATH', 'token.json')
CREDENTIALS_PATH = os.environ.get('CREDENTIALS_PATH', 'credentials.json')
SERVICE_ACCOUNT_PATH = os.environ.get('SERVICE_ACCOUNT_PATH', 'service_account.json')
DRIVE_FOLDER_ID = os.environ.get('DRIVE_FOLDER_ID')


@dataclass
class SpreadsheetContext:
    sheets_service: Any
    drive_service: Any
    folder_id: Optional[str] = None


@asynccontextmanager
async def spreadsheet_lifespan(server: FastMCP) -> AsyncIterator[SpreadsheetContext]:
    """Create Sheets & Drive service on startup and reuse across requests"""
    creds = None
    if CREDENTIALS_CONFIG:
        creds = service_account.Credentials.from_service_account_info(
            json.loads(base64.b64decode(CREDENTIALS_CONFIG)), SCOPES)

    if SERVICE_ACCOUNT_PATH and os.path.exists(SERVICE_ACCOUNT_PATH):
        try:
            creds = service_account.Credentials.from_service_account_file(
                SERVICE_ACCOUNT_PATH, scopes=SCOPES)
            print("Using service account authentication")
        except Exception as e:
            print(f"Service account auth failed: {e}")
            creds = None

    if not creds:
        print("Falling back to OAuth flow")
        if os.path.exists(TOKEN_PATH):
            with open(TOKEN_PATH, 'r') as token_file:
                creds = Credentials.from_authorized_user_info(json.load(token_file), SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
                creds = flow.run_local_server(port=0)
            with open(TOKEN_PATH, 'w') as token_file:
                token_file.write(creds.to_json())

    sheets_service = build('sheets', 'v4', credentials=creds)
    drive_service = build('drive', 'v3', credentials=creds)
    try:
        yield SpreadsheetContext(sheets_service=sheets_service, drive_service=drive_service, folder_id=DRIVE_FOLDER_ID)
    finally:
        pass


mcp = FastMCP(
    "Google Spreadsheet",
    dependencies=["google-auth", "google-auth-oauthlib", "google-api-python-client"],
    lifespan=spreadsheet_lifespan,
)

# Example tool ported from existing code; more tools will be migrated incrementally

@mcp.tool()
def list_sheets(spreadsheet_id: str, ctx: Context = None) -> List[str]:
    """List sheet names in spreadsheet"""
    sheets_service = ctx.request_context.lifespan_context.sheets_service
    spreadsheet = sheets_service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    return [s['properties']['title'] for s in spreadsheet.get('sheets', [])]


@mcp.tool()
def create_spreadsheet(title: str, sheets: Optional[List[str]] = None, ctx: Context = None) -> Dict[str, Any]:
    """Create a new spreadsheet, optionally within configured Drive folder."""
    folder_id = ctx.request_context.lifespan_context.folder_id
    return _create_spreadsheet_impl(title=title, sheets=sheets, folder_id=folder_id)


@mcp.tool()
def get_spreadsheet(spreadsheet_id: str, include_grid_data: bool = False, ctx: Context = None) -> Dict[str, Any]:
    return _get_spreadsheet_impl(spreadsheet_id=spreadsheet_id, include_grid_data=include_grid_data)


@mcp.tool()
def list_spreadsheets(query: Optional[str] = None, page_size: int = 20, page_token: Optional[str] = None, order_by: Optional[str] = None, ctx: Context = None) -> Dict[str, Any]:
    return _list_spreadsheets_impl(query=query, page_size=page_size, page_token=page_token, order_by=order_by)


@mcp.tool()
def get_values(spreadsheet_id: str, range_name: str, value_render_option: str = "FORMATTED_VALUE", ctx: Context = None) -> Dict[str, Any]:
    return _get_values_impl(spreadsheet_id=spreadsheet_id, range_name=range_name, value_render_option=value_render_option)


@mcp.tool()
def update_values(spreadsheet_id: str, range_name: str, values: List[List[Any]], value_input_option: str = "RAW", ctx: Context = None) -> Dict[str, Any]:
    return _update_values_impl(spreadsheet_id=spreadsheet_id, range_name=range_name, values=values, value_input_option=value_input_option)


@mcp.tool()
def append_values(spreadsheet_id: str, range_name: str, values: List[List[Any]], value_input_option: str = "RAW", insert_data_option: str = "INSERT_ROWS", ctx: Context = None) -> Dict[str, Any]:
    return _append_values_impl(spreadsheet_id=spreadsheet_id, range_name=range_name, values=values, value_input_option=value_input_option, insert_data_option=insert_data_option)


@mcp.tool()
def clear_values(spreadsheet_id: str, range_name: str, ctx: Context = None) -> Dict[str, Any]:
    return _clear_values_impl(spreadsheet_id=spreadsheet_id, range_name=range_name)


@mcp.tool()
def add_sheet(spreadsheet_id: str, title: str, rows: int = 1000, columns: int = 26, ctx: Context = None) -> Dict[str, Any]:
    return _add_sheet_impl(spreadsheet_id=spreadsheet_id, title=title, rows=rows, columns=columns)


@mcp.tool()
def delete_sheet(spreadsheet_id: str, sheet_id: int, ctx: Context = None) -> Dict[str, Any]:
    return _delete_sheet_impl(spreadsheet_id=spreadsheet_id, sheet_id=sheet_id)


@mcp.tool()
def rename_sheet(spreadsheet_id: str, sheet_id: int, new_title: str, ctx: Context = None) -> Dict[str, Any]:
    return _rename_sheet_impl(spreadsheet_id=spreadsheet_id, sheet_id=sheet_id, new_title=new_title)


@mcp.tool()
def share_spreadsheet(spreadsheet_id: str, recipients: List[Dict[str, str]], send_notification: bool = False, ctx: Context = None) -> Dict[str, Any]:
    return _share_spreadsheet_impl(spreadsheet_id=spreadsheet_id, permissions=recipients, send_notification=send_notification)


def main():  # pragma: no cover
    mcp.run()


if __name__ == "__main__":
    main() 