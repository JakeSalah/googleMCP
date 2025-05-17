#!/usr/bin/env python3
"""
Minimal FastMCP server for testing.
This is a self-contained file that doesn't depend on other modules.
"""

import os
import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

# Import directly from mcp package
from mcp.server.fastmcp import FastMCP, Context


@dataclass
class ServerContext:
    """Simple context for the server"""
    initialized: bool = True


@asynccontextmanager
async def server_lifespan(server: FastMCP) -> AsyncIterator[ServerContext]:
    """Setup and teardown for the server"""
    print("Starting basic FastMCP server...")
    try:
        yield ServerContext()
    finally:
        print("Shutting down basic FastMCP server...")


# Create a FastMCP server with a name
mcp = FastMCP(
    "Basic Test Server",
    lifespan=server_lifespan,
)


@mcp.tool()
def echo(message: str, ctx: Context = None) -> str:
    """Simple echo tool that returns the input message"""
    return f"Echo: {message}"


@mcp.tool()
def add(a: float, b: float, ctx: Context = None) -> float:
    """Add two numbers together"""
    return a + b


@mcp.resource("greeting://{name}")
def greeting(name: str) -> str:
    """A simple greeting resource"""
    return f"Hello, {name}!"


if __name__ == "__main__":
    # Set PORT environment variable to configure the server port
    port = os.environ.get("PORT", "8080")
    os.environ["PORT"] = port
    print(f"Starting server with PORT={port}")
    mcp.run() 