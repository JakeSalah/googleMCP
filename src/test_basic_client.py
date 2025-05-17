#!/usr/bin/env python3
"""
Test client for basic_fastmcp_server.py
"""

import json
import asyncio
import logging
import sys
import subprocess
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_client")

async def send_request(proc, request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Send a request to the server and get the response"""
    request_str = json.dumps(request_data) + "\n"
    logger.info(f"Sending: {request_str.strip()}")
    
    proc.stdin.write(request_str.encode('utf-8'))
    await proc.stdin.drain()
    
    response_line = await proc.stdout.readline()
    response = json.loads(response_line.decode('utf-8'))
    logger.info(f"Received: {response}")
    
    return response

async def test_server():
    """Run tests against the server"""
    # Start the server process
    cmd = ["python3", "basic_fastmcp_server.py"]
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env={"PORT": "8080"}
    )
    
    logger.info("Server process started")
    
    try:
        # Test echo tool
        echo_request = {
            "jsonrpc": "2.0",
            "method": "echo",
            "params": {"message": "Hello, FastMCP!"},
            "id": 1
        }
        
        echo_response = await send_request(proc, echo_request)
        assert echo_response.get("result") == "Echo: Hello, FastMCP!", "Echo test failed"
        
        # Test add tool
        add_request = {
            "jsonrpc": "2.0",
            "method": "add",
            "params": {"a": 5, "b": 3},
            "id": 2
        }
        
        add_response = await send_request(proc, add_request)
        assert add_response.get("result") == 8, "Add test failed"
        
        logger.info("All tests passed!")
        
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
    finally:
        # Terminate the server process
        proc.terminate()
        await proc.wait()
        logger.info("Server process terminated")

if __name__ == "__main__":
    asyncio.run(test_server()) 