# Google MCPs FastMCP Implementation

This repository contains a clean implementation of Google MCPs using the FastMCP architecture.

## Structure

- `src/basic_fastmcp_server.py` - A minimal FastMCP server for testing
- `src/fast_sheets_server.py` - A standalone FastMCP server for Google Sheets
- `src/stop_fast_mcps.sh` - Script to stop all FastMCP servers
- `src/mcp_google_sheets/` - Google Sheets implementation using FastMCP
- `src/mcp_google_calendar/` - Google Calendar implementation
- `src/mcp_google_docs/` - Google Docs implementation
- `src/mcp_google_drive/` - Google Drive implementation
- `src/mcp_google_gmail/` - Gmail implementation
- `src/mcp_google_meet/` - Google Meet implementation
- `src/mcp_google_shared/` - Shared utilities for Google services

## Getting Started

To run the basic FastMCP server:

```
cd src
python basic_fastmcp_server.py
```

To run the Google Sheets FastMCP server:

```
cd src
python fast_sheets_server.py
``` 