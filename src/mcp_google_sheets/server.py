"""
Simple FastMCP server for Google Sheets.
"""

import os
from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP

from src.mcp_google_sheets import mcp

# Create a FastAPI app for the server
app = FastAPI(title="Google Sheets MCP")

# Add the MCP router to the app
app.include_router(mcp.router, prefix="/ai")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}

def start_server():
    """Start the server using uvicorn."""
    import uvicorn
    port = int(os.environ.get("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    start_server() 