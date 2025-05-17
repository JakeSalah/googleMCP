# Google FastMCP Servers

This package provides FastMCP-based servers for Google services, reimplementing the existing Google MCPs in a more scalable architecture.

## Features

- ✅ Full compatibility with existing Google MCPs functionality
- 🔄 Asynchronous lifespan management for better resource handling
- 🔐 Improved authentication flow (Service Account → OAuth fallback)
- 🛠️ Simplified deployment and maintenance
- 📊 Better performance at scale

## Installation

```
pip install -e .
```

## Services

The package includes FastMCP servers for:

- **Google Sheets**: Spreadsheet operations
- **Google Drive**: File storage and management 
- **Google Gmail**: Email operations
- **Google Calendar**: Calendar and event management
- **Google Docs**: Document creation and editing
- **Google Meet**: Video meeting management

## Running Servers

Use the provided script:

```bash
./start_fast_mcps.sh
```

Or run individual servers:

```bash
python -m src.mcp_google_sheets
python -m src.mcp_google_drive
# etc.
```

## Configuration

Set these environment variables:

- `SERVICE_ACCOUNT_PATH`: Path to service account credentials
- `CREDENTIALS_PATH`: Path to OAuth client credentials
- `TOKEN_PATH`: Path where OAuth tokens will be stored
- `DRIVE_FOLDER_ID`: (Optional) Default Google Drive folder for new files

## Resources

- [FastMCP Documentation](https://github.com/xing5/mcp-google-sheets)
- [Google API Python Client](https://github.com/googleapis/google-api-python-client) 