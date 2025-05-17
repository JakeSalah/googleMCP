#!/usr/bin/env python3
"""
Test client for the FastMCP Sheets server using HTTP requests
"""

import os
import json
import asyncio
import logging
import requests
import subprocess
import time
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("sheets_test_client")

def start_server():
    """Start the server in the background"""
    logger.info("Starting sheets server...")
    cmd = ["python3", "fast_sheets_server.py"]
    env = os.environ.copy()
    env["PORT"] = "8001"
    
    # Start the server process and return it
    proc = subprocess.Popen(
        cmd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Give the server time to start
    time.sleep(2)
    return proc

def check_server_health():
    """Check if the server is up by accessing the SSE endpoint"""
    url = "http://localhost:8000/sse"
    logger.info(f"Checking server health at {url}")
    
    try:
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            logger.info("Server is up and running!")
            # Close the stream
            response.close()
            return True
        else:
            logger.error(f"Server health check failed: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Cannot connect to server: {e}")
        return False

def get_sse_session():
    """Connect to the SSE endpoint and get a session ID"""
    url = "http://localhost:8000/sse"
    logger.info(f"Connecting to SSE endpoint at {url}")
    
    try:
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            # Read the first event to get the session ID
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    if decoded_line.startswith('data: /messages/?session_id='):
                        session_id = decoded_line.split('=')[1]
                        logger.info(f"Got session ID: {session_id}")
                        response.close()
                        return session_id
            
            response.close()
            logger.error("Could not find session ID in SSE response")
            return None
        else:
            logger.error(f"SSE connection failed: {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"Error connecting to SSE: {e}")
        return None

def test_create_spreadsheet(session_id):
    """Test the create_spreadsheet tool via HTTP"""
    url = f"http://localhost:8000/messages/?session_id={session_id}"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    data = {
        "jsonrpc": "2.0",
        "method": "create_spreadsheet",
        "params": {
            "title": "Test Spreadsheet",
            "sheets": ["Sheet1", "Sheet2"]
        },
        "id": 1
    }
    
    logger.info(f"Sending request to {url}")
    response = requests.post(url, headers=headers, json=data)
    
    # 202 Accepted is a success for async processing
    if response.status_code in [200, 202]:
        logger.info(f"Request accepted with status code: {response.status_code}")
        return True
    else:
        logger.error(f"Error: {response.status_code}, {response.text}")
        return False

def test_get_spreadsheet(session_id):
    """Test the get_spreadsheet tool via HTTP"""
    url = f"http://localhost:8000/messages/?session_id={session_id}"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    data = {
        "jsonrpc": "2.0",
        "method": "get_spreadsheet",
        "params": {
            "spreadsheet_id": "1234567890abcdefgh"
        },
        "id": 2
    }
    
    logger.info(f"Sending request to {url}")
    response = requests.post(url, headers=headers, json=data)
    
    # 202 Accepted is a success for async processing
    if response.status_code in [200, 202]:
        logger.info(f"Request accepted with status code: {response.status_code}")
        return True
    else:
        logger.error(f"Error: {response.status_code}, {response.text}")
        return False

if __name__ == "__main__":
    # Start the server
    server_proc = start_server()
    
    try:
        # First check if the server is healthy
        if check_server_health():
            # Get a session ID
            session_id = get_sse_session()
            
            if session_id:
                # Run the tests
                create_result = test_create_spreadsheet(session_id)
                get_result = test_get_spreadsheet(session_id)
                
                if create_result and get_result:
                    logger.info("All tests passed!")
                else:
                    logger.error("Some tests failed")
            else:
                logger.error("Failed to get session ID, skipping tests")
        else:
            logger.error("Server health check failed, skipping tests")
            
    except Exception as e:
        logger.error(f"Error during testing: {e}", exc_info=True)
    finally:
        # Terminate the server
        logger.info("Terminating server...")
        server_proc.terminate()
        server_proc.wait() 