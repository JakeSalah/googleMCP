#!/bin/bash

# stop_fast_mcps.sh
# Stops all Google FastMCP servers

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
SESSION_NAME="google_fastmcps"

# Check if tmux is installed
if ! command -v tmux &> /dev/null; then
    echo -e "${RED}Error: tmux is not installed. Please install tmux to continue.${NC}"
    exit 1
fi

# Check if the session exists
if ! tmux has-session -t $SESSION_NAME 2>/dev/null; then
    echo -e "${RED}No FastMCP servers are running (tmux session $SESSION_NAME not found).${NC}"
    exit 0
fi

# Kill the session
echo -e "Stopping all FastMCP servers..."
tmux kill-session -t $SESSION_NAME
echo -e "${GREEN}All FastMCP servers have been stopped.${NC}" 