#!/usr/bin/env python3
"""
Standalone FastAPI-based FastMCP server for Google Sheets.
This is a test server to verify the FastMCP installation works.
"""

import os
import json
import base64
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

import uvicorn

# Direct import from mcp.server.fastmcp
from mcp.server.fastmcp import FastMCP, Context

# Configuration
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
SERVICE_ACCOUNT_PATH = os.environ.get("SERVICE_ACCOUNT_PATH", "service_account.json")
DRIVE_FOLDER_ID = os.environ.get("DRIVE_FOLDER_ID", "")

# Dataclass for the service context
@dataclass
class SpreadsheetContext:
    """Context for Spreadsheet service"""
    sheets_service: Any = None
    drive_service: Any = None
    folder_id: Optional[str] = None

# Async context manager for server lifespan 
@asynccontextmanager
async def spreadsheet_lifespan(server: FastMCP) -> AsyncIterator[SpreadsheetContext]:
    """For test purposes, just yield a minimal context without actually authenticating"""
    print("Starting spreadsheet server...")
    try:
        yield SpreadsheetContext(folder_id=DRIVE_FOLDER_ID)
    finally:
        print("Shutting down spreadsheet server...")

# Create the FastMCP server
mcp = FastMCP(
    "Google Sheets Test",
    dependencies=["google-auth", "google-auth-oauthlib", "google-api-python-client"],
    lifespan=spreadsheet_lifespan,
)

# Define tools
@mcp.tool()
def create_spreadsheet(title: str, sheets: Optional[List[str]] = None, ctx: Context = None) -> Dict[str, Any]:
    """Create a new spreadsheet, optionally within configured Drive folder."""
    # Just return a dummy response for testing
    return {
        "success": True,
        "spreadsheet_id": "1234567890abcdefgh",
        "title": title,
        "sheets": sheets or ["Sheet1"],
        "url": f"https://docs.google.com/spreadsheets/d/1234567890abcdefgh/edit"
    }

@mcp.tool()
def get_spreadsheet(spreadsheet_id: str, ctx: Context = None) -> Dict[str, Any]:
    """Get a spreadsheet by ID."""
    # Return dummy response
    return {
        "spreadsheet_id": spreadsheet_id,
        "title": "Test Spreadsheet",
        "sheets": ["Sheet1", "Sheet2"],
        "url": f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit"
    }

# Main entry point
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8001))
    print(f"Starting FastMCP server on port {port}...")
    
    # For a FastAPI-compatible server, we need to use 'sse' transport 
    # which will create a Starlette-compatible app internally
    os.environ["PORT"] = str(port)
    mcp.run(transport="sse")
    
    # Note: You could also use streamable-http transport
    # mcp.run(transport="streamable-http") 