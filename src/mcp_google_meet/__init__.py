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

from services.meet.app.google_meet import (
    create_meeting as _create_meet_impl,
    get_meeting as _get_meet_impl,
    update_meeting as _update_meet_impl,
    delete_meeting as _delete_meet_impl,
    list_meetings as _list_meet_impl,
    add_attendee as _add_attendee_impl,
    remove_attendee as _remove_attendee_impl,
    update_attendee_status as _update_status_impl,
    get_join_info as _get_join_info_impl,
    share_meeting as _share_meet_impl,
)

SCOPES = ["https://www.googleapis.com/auth/calendar"]
CREDENTIALS_CONFIG = os.environ.get("CREDENTIALS_CONFIG")
TOKEN_PATH = os.environ.get("TOKEN_PATH", "token.json")
CREDENTIALS_PATH = os.environ.get("CREDENTIALS_PATH", "credentials.json")
SERVICE_ACCOUNT_PATH = os.environ.get("SERVICE_ACCOUNT_PATH", "service_account.json")


@dataclass
class MeetContext:
    calendar_service: Any


@asynccontextmanager
async def meet_lifespan(server: FastMCP) -> AsyncIterator[MeetContext]:
    creds = None
    if CREDENTIALS_CONFIG:
        creds = service_account.Credentials.from_service_account_info(json.loads(base64.b64decode(CREDENTIALS_CONFIG)), SCOPES)

    if SERVICE_ACCOUNT_PATH and os.path.exists(SERVICE_ACCOUNT_PATH):
        try:
            creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_PATH, scopes=SCOPES)
            print("Using service account auth (Meet)")
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

    calendar_service = build("calendar", "v3", credentials=creds)
    try:
        yield MeetContext(calendar_service=calendar_service)
    finally:
        pass


mcp = FastMCP(
    "Google Meet",
    dependencies=["google-auth", "google-auth-oauthlib", "google-api-python-client"],
    lifespan=meet_lifespan,
)

# Tools
@mcp.tool()
def meet_create(title: str, description: Optional[str] = None, start_time: str = None, end_time: Optional[str] = None, time_zone: str = "UTC", attendees: Optional[List[Dict]] = None, send_notifications: bool = True, ctx: Context = None) -> Dict[str, Any]:
    return _create_meet_impl(title=title, description=description, start_time=start_time, end_time=end_time, time_zone=time_zone, attendees=attendees, send_notifications=send_notifications)

@mcp.tool()
def meet_get(meeting_id: str, ctx: Context = None) -> Dict[str, Any]:
    return _get_meet_impl(meeting_id=meeting_id)

@mcp.tool()
def meet_update(meeting_id: str, ctx: Context = None, **kwargs) -> Dict[str, Any]:
    return _update_meet_impl(meeting_id=meeting_id, **kwargs)

@mcp.tool()
def meet_delete(meeting_id: str, send_notifications: bool = True, ctx: Context = None) -> Dict[str, Any]:
    return _delete_meet_impl(meeting_id=meeting_id, send_notifications=send_notifications)

@mcp.tool()
def meet_list(ctx: Context = None, **kwargs) -> Dict[str, Any]:
    return _list_meet_impl(**kwargs)

@mcp.tool()
def meet_add_attendee(meeting_id: str, attendee: Dict, send_notifications: bool = True, ctx: Context = None) -> Dict[str, Any]:
    return _add_attendee_impl(meeting_id=meeting_id, attendee=attendee, send_notifications=send_notifications)

@mcp.tool()
def meet_remove_attendee(meeting_id: str, email: str, send_notifications: bool = True, ctx: Context = None) -> Dict[str, Any]:
    return _remove_attendee_impl(meeting_id=meeting_id, email=email, send_notifications=send_notifications)

@mcp.tool()
def meet_update_attendee_status(meeting_id: str, email: str, response_status: str, ctx: Context = None) -> Dict[str, Any]:
    return _update_status_impl(meeting_id=meeting_id, email=email, response_status=response_status)

@mcp.tool()
def meet_get_join_info(meeting_id: str, ctx: Context = None) -> Dict[str, Any]:
    return _get_join_info_impl(meeting_id=meeting_id)

@mcp.tool()
def meet_share(meeting_id: str, rule: Dict[str, str], ctx: Context = None) -> Dict[str, Any]:
    return _share_meet_impl(meeting_id=meeting_id, **rule)


def main():
    mcp.run()


if __name__ == "__main__":
    main() 