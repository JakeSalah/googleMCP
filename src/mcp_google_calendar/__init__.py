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

from services.calendar.app.google_calendar import (
    create_calendar as _create_calendar_impl,
    get_calendar as _get_calendar_impl,
    update_calendar as _update_calendar_impl,
    delete_calendar as _delete_calendar_impl,
    list_calendars as _list_calendars_impl,
    share_calendar as _share_calendar_impl,
    create_event as _create_event_impl,
    get_event as _get_event_impl,
    update_event as _update_event_impl,
    delete_event as _delete_event_impl,
    list_events as _list_events_impl,
    quick_add_event as _quick_add_impl,
    move_event as _move_event_impl,
    import_event as _import_event_impl,
    check_free_busy as _check_free_busy_impl,
)

SCOPES = ["https://www.googleapis.com/auth/calendar"]
CREDENTIALS_CONFIG = os.environ.get("CREDENTIALS_CONFIG")
TOKEN_PATH = os.environ.get("TOKEN_PATH", "token.json")
CREDENTIALS_PATH = os.environ.get("CREDENTIALS_PATH", "credentials.json")
SERVICE_ACCOUNT_PATH = os.environ.get("SERVICE_ACCOUNT_PATH", "service_account.json")


@dataclass
class CalendarContext:
    calendar_service: Any


@asynccontextmanager
async def calendar_lifespan(server: FastMCP) -> AsyncIterator[CalendarContext]:
    creds = None
    if CREDENTIALS_CONFIG:
        creds = service_account.Credentials.from_service_account_info(
            json.loads(base64.b64decode(CREDENTIALS_CONFIG)), SCOPES)

    if SERVICE_ACCOUNT_PATH and os.path.exists(SERVICE_ACCOUNT_PATH):
        try:
            creds = service_account.Credentials.from_service_account_file(
                SERVICE_ACCOUNT_PATH, scopes=SCOPES)
            print("Using service account authentication (Calendar)")
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

    calendar_service = build("calendar", "v3", credentials=creds)
    try:
        yield CalendarContext(calendar_service=calendar_service)
    finally:
        pass


mcp = FastMCP(
    "Google Calendar",
    dependencies=["google-auth", "google-auth-oauthlib", "google-api-python-client"],
    lifespan=calendar_lifespan,
)

# Calendar tools
@mcp.tool()
def calendar_create(summary: str, description: Optional[str] = None, location: Optional[str] = None, time_zone: Optional[str] = None, ctx: Context = None) -> Dict[str, Any]:
    return _create_calendar_impl(summary=summary, description=description, location=location, time_zone=time_zone)

@mcp.tool()
def calendar_get(calendar_id: str, ctx: Context = None) -> Dict[str, Any]:
    return _get_calendar_impl(calendar_id=calendar_id)

@mcp.tool()
def calendar_update(calendar_id: str, summary: Optional[str] = None, description: Optional[str] = None, location: Optional[str] = None, time_zone: Optional[str] = None, ctx: Context = None) -> Dict[str, Any]:
    return _update_calendar_impl(calendar_id=calendar_id, summary=summary, description=description, location=location, time_zone=time_zone)

@mcp.tool()
def calendar_delete(calendar_id: str, ctx: Context = None) -> Dict[str, Any]:
    return _delete_calendar_impl(calendar_id=calendar_id)

@mcp.tool()
def calendar_list(show_hidden: bool = False, min_access_role: Optional[str] = None, ctx: Context = None) -> Dict[str, Any]:
    return _list_calendars_impl(show_hidden=show_hidden, min_access_role=min_access_role)

@mcp.tool()
def calendar_share(calendar_id: str, scope_type: str, role: str, scope_value: Optional[str] = None, ctx: Context = None) -> Dict[str, Any]:
    return _share_calendar_impl(calendar_id=calendar_id, scope_type=scope_type, role=role, scope_value=scope_value)

# Event tools
@mcp.tool()
def event_create(calendar_id: str, summary: str, start: Dict[str, Any], end: Dict[str, Any], ctx: Context = None, **kwargs) -> Dict[str, Any]:
    return _create_event_impl(calendar_id=calendar_id, summary=summary, start=start, end=end, **kwargs)

@mcp.tool()
def event_get(calendar_id: str, event_id: str, time_zone: Optional[str] = None, ctx: Context = None) -> Dict[str, Any]:
    return _get_event_impl(calendar_id=calendar_id, event_id=event_id, time_zone=time_zone)

@mcp.tool()
def event_update(calendar_id: str, event_id: str, ctx: Context = None, **kwargs) -> Dict[str, Any]:
    return _update_event_impl(calendar_id=calendar_id, event_id=event_id, **kwargs)

@mcp.tool()
def event_delete(calendar_id: str, event_id: str, send_notifications: bool = False, ctx: Context = None) -> Dict[str, Any]:
    return _delete_event_impl(calendar_id=calendar_id, event_id=event_id, send_notifications=send_notifications)

@mcp.tool()
def event_list(calendar_id: str, ctx: Context = None, **kwargs) -> Dict[str, Any]:
    return _list_events_impl(calendar_id=calendar_id, **kwargs)

@mcp.tool()
def event_quick_add(calendar_id: str, text: str, send_notifications: bool = False, ctx: Context = None) -> Dict[str, Any]:
    return _quick_add_impl(calendar_id=calendar_id, text=text, send_notifications=send_notifications)

@mcp.tool()
def event_move(source_calendar_id: str, destination_calendar_id: str, event_id: str, send_notifications: bool = False, ctx: Context = None) -> Dict[str, Any]:
    return _move_event_impl(source_calendar_id=source_calendar_id, destination_calendar_id=destination_calendar_id, event_id=event_id, send_notifications=send_notifications)

@mcp.tool()
def event_import(calendar_id: str, ical_data: str, send_notifications: bool = False, ctx: Context = None) -> Dict[str, Any]:
    return _import_event_impl(calendar_id=calendar_id, ical_data=ical_data, send_notifications=send_notifications)

@mcp.tool()
def calendar_free_busy(time_min: str, time_max: str, calendar_ids: List[str], time_zone: Optional[str] = None, ctx: Context = None) -> Dict[str, Any]:
    return _check_free_busy_impl(time_min=time_min, time_max=time_max, calendar_ids=calendar_ids, time_zone=time_zone)


def main():
    mcp.run()


if __name__ == "__main__":
    main() 