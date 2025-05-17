#!/usr/bin/env python3
"""
Minimal FastMCP server for testing.
This is a self-contained file that doesn't depend on other modules.
"""

import os
import asyncio
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

# Import directly from mcp package
from mcp.server.fastmcp import FastMCP, Context

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("basic_fastmcp_server")


@dataclass
class ServerContext:
    """Simple context for the server"""
    initialized: bool = True


@asynccontextmanager
async def server_lifespan(server: FastMCP) -> AsyncIterator[ServerContext]:
    """Setup and teardown for the server"""
    logger.info("Starting basic FastMCP server...")
    try:
        yield ServerContext()
    finally:
        logger.info("Shutting down basic FastMCP server...")


# Create a FastMCP server with a name
mcp = FastMCP(
    "Basic Test Server",
    lifespan=server_lifespan,
)


@mcp.tool()
def echo(message: str, ctx: Context = None) -> str:
    """Simple echo tool that returns the input message"""
    logger.info(f"Echo called with message: {message}")
    return f"Echo: {message}"


@mcp.tool()
def add(a: float, b: float, ctx: Context = None) -> float:
    """Add two numbers together"""
    logger.info(f"Add called with values: {a} and {b}")
    return a + b


@mcp.resource("greeting://{name}")
def greeting(name: str) -> str:
    """A simple greeting resource"""
    logger.info(f"Greeting resource accessed for: {name}")
    return f"Hello, {name}!"


if __name__ == "__main__":
    # Set PORT environment variable to configure the server port
    port = os.environ.get("PORT", "8080")
    os.environ["PORT"] = port
    
    logger.info(f"Starting server with PORT={port}")
    
    try:
        # Specify stdio transport for basic testing
        mcp.run(transport="stdio")
    except KeyboardInterrupt:
        logger.info("Server shutdown requested via keyboard interrupt")
    except Exception as e:
        logger.error(f"Error running server: {e}", exc_info=True)
    finally:
        logger.info("Server stopped") 