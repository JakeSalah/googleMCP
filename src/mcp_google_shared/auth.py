"""
Authentication utilities for Google MCPs
"""

import base64
import json
import os
from typing import List, Any, Optional
import logging

from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Default paths
CREDENTIALS_CONFIG = os.environ.get('CREDENTIALS_CONFIG')
TOKEN_PATH = os.environ.get('TOKEN_PATH', 'token.json')
CREDENTIALS_PATH = os.environ.get('CREDENTIALS_PATH', 'credentials.json')
SERVICE_ACCOUNT_PATH = os.environ.get('SERVICE_ACCOUNT_PATH', 'service_account.json')

logger = logging.getLogger(__name__)

def get_credentials(scopes: List[str]) -> Any:
    """
    Get OAuth credentials using various methods.
    
    Tries in this order:
    1. Use base64 encoded credentials from CREDENTIALS_CONFIG env var
    2. Use service account file from SERVICE_ACCOUNT_PATH env var
    3. Use OAuth flow from CREDENTIALS_PATH/TOKEN_PATH
    
    Args:
        scopes: List of OAuth scopes needed
        
    Returns:
        Google Auth credentials object or None if all auth methods fail
    """
    creds = None
    
    # 1. Try credentials from environment var (base64 encoded)
    if CREDENTIALS_CONFIG:
        try:
            creds = service_account.Credentials.from_service_account_info(
                json.loads(base64.b64decode(CREDENTIALS_CONFIG)), scopes)
            logger.info("Using credentials from CREDENTIALS_CONFIG environment variable")
            return creds
        except Exception as e:
            logger.warning(f"Failed to load credentials from CREDENTIALS_CONFIG: {e}")
    
    # 2. Try service account auth
    if SERVICE_ACCOUNT_PATH and os.path.exists(SERVICE_ACCOUNT_PATH):
        try:
            creds = service_account.Credentials.from_service_account_file(
                SERVICE_ACCOUNT_PATH, scopes=scopes)
            logger.info(f"Using service account authentication from {SERVICE_ACCOUNT_PATH}")
            return creds
        except Exception as e:
            logger.warning(f"Service account auth failed: {e}")
    
    # 3. Try OAuth flow with saved token
    if os.path.exists(TOKEN_PATH):
        try:
            with open(TOKEN_PATH, "r") as tf:
                creds = Credentials.from_authorized_user_info(json.load(tf), scopes)
            logger.info(f"Loaded OAuth credentials from {TOKEN_PATH}")
        except Exception as e:
            logger.warning(f"Failed to load OAuth token: {e}")
    
    # 4. Refresh token if expired or get new tokens
    try:
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                logger.info("Refreshed OAuth token")
            else:
                # Interactive OAuth flow - requires browser
                if not os.path.exists(CREDENTIALS_PATH):
                    logger.error(f"OAuth credentials not found at {CREDENTIALS_PATH}")
                    return None
                    
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, scopes)
                creds = flow.run_local_server(port=0)
                logger.info("Completed OAuth flow with browser sign-in")
            
            # Save the credentials for next run
            try:
                with open(TOKEN_PATH, "w") as tf:
                    tf.write(creds.to_json())
                logger.info(f"Saved OAuth credentials to {TOKEN_PATH}")
            except Exception as e:
                logger.warning(f"Failed to save OAuth token: {e}")
    except Exception as e:
        logger.error(f"Auth error: {e}")
        return None
        
    return creds

def create_service(api_name: str, api_version: str, scopes: List[str]) -> Optional[Any]:
    """
    Create a Google API service with proper authentication.
    
    Args:
        api_name: Name of the Google API (e.g., 'drive', 'sheets')
        api_version: API version (e.g., 'v3')
        scopes: List of OAuth scopes needed
        
    Returns:
        Google API service or None if authentication fails
    """
    creds = get_credentials(scopes)
    if not creds:
        logger.error(f"Failed to get valid credentials for {api_name}")
        return None
        
    try:
        service = build(api_name, api_version, credentials=creds)
        logger.info(f"Created {api_name} service")
        return service
    except Exception as e:
        logger.error(f"Failed to create {api_name} service: {e}")
        return None 