#!/usr/bin/env bash
# Stop Home Assistant
# This script stops a running Home Assistant instance

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PID_FILE="$PROJECT_ROOT/.ha_pid"

# Parse arguments
FORCE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -f|--force)
            FORCE=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -f, --force    Force kill if graceful shutdown fails"
            echo "  -h, --help     Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}🏠 Stopping Home Assistant${NC}"
echo ""

# Function to kill process by PID
kill_by_pid() {
    local pid=$1
    local force=$2
    
    if [ "$force" = true ]; then
        echo -e "${YELLOW}⚠️  Force killing process $pid...${NC}"
        kill -9 "$pid" 2>/dev/null || true
    else
        echo -e "${BLUE}➡️  Sending SIGTERM to process $pid...${NC}"
        kill "$pid" 2>/dev/null || true
        
        # Wait up to 10 seconds for graceful shutdown
        local count=0
        while kill -0 "$pid" 2>/dev/null && [ $count -lt 10 ]; do
            sleep 1
            count=$((count + 1))
        done
        
        # If still running, force kill
        if kill -0 "$pid" 2>/dev/null; then
            echo -e "${YELLOW}⚠️  Graceful shutdown failed. Force killing...${NC}"
            kill -9 "$pid" 2>/dev/null || true
        fi
    fi
}

# Check if PID file exists
if [ -f "$PID_FILE" ]; then
    HA_PID=$(cat "$PID_FILE")
    
    # Check if process is running
    if kill -0 "$HA_PID" 2>/dev/null; then
        kill_by_pid "$HA_PID" "$FORCE"
        
        # Verify process is stopped
        if ! kill -0 "$HA_PID" 2>/dev/null; then
            echo -e "${GREEN}✅ Home Assistant stopped (PID: $HA_PID)${NC}"
            rm -f "$PID_FILE"
        else
            echo -e "${RED}❌ Failed to stop Home Assistant${NC}"
            exit 1
        fi
    else
        echo -e "${YELLOW}⚠️  Process $HA_PID not running (stale PID file)${NC}"
        rm -f "$PID_FILE"
    fi
else
    # No PID file, try to find Home Assistant processes
    echo -e "${YELLOW}⚠️  No PID file found. Searching for Home Assistant processes...${NC}"
    
    # Find Home Assistant processes
    HA_PIDS=$(pgrep -f "python.*homeassistant" || true)
    
    if [ -n "$HA_PIDS" ]; then
        echo -e "${BLUE}Found Home Assistant processes:${NC}"
        for pid in $HA_PIDS; do
            ps -p "$pid" -o pid,cmd --no-headers 2>/dev/null || true
        done
        echo ""
        
        # Ask for confirmation if not forcing
        if [ "$FORCE" = false ]; then
            read -p "Stop these processes? (y/N): " -n 1 -r
            echo ""
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                echo -e "${YELLOW}⚠️  Cancelled${NC}"
                exit 0
            fi
        fi
        
        # Kill all found processes
        for pid in $HA_PIDS; do
            kill_by_pid "$pid" "$FORCE"
        done
        
        echo -e "${GREEN}✅ All Home Assistant processes stopped${NC}"
    else
        echo -e "${GREEN}✅ No Home Assistant processes found${NC}"
    fi
fi

echo ""
echo -e "${GREEN}✅ Home Assistant stopped successfully${NC}"
