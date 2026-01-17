#!/usr/bin/env bash
# Start Home Assistant for Development
# This script starts Home Assistant with the development configuration

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
CONFIG_DIR="$PROJECT_ROOT/config"
VENV_PATH="$PROJECT_ROOT/.venv"

# Parse arguments
BACKGROUND=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -b|--background)
            BACKGROUND=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -b, --background    Run Home Assistant in the background"
            echo "  -v, --verbose       Enable verbose logging"
            echo "  -h, --help          Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}🏠 Starting Home Assistant for Development${NC}"
echo ""

# Check if virtual environment exists
if [ ! -d "$VENV_PATH" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not found. Running setup script...${NC}"
    bash "$SCRIPT_DIR/setup_dev_environment.sh"
fi

# Activate virtual environment
if [ -f "$VENV_PATH/bin/activate" ]; then
    source "$VENV_PATH/bin/activate"
elif [ -f "$VENV_PATH/Scripts/activate" ]; then
    source "$VENV_PATH/Scripts/activate"
else
    echo -e "${RED}❌ Could not find virtual environment activation script${NC}"
    exit 1
fi

# Check if Home Assistant is installed
if ! python -c "import homeassistant" &> /dev/null; then
    echo -e "${RED}❌ Home Assistant not found. Installing...${NC}"
    pip install homeassistant
fi

# Create config directory if it doesn't exist
if [ ! -d "$CONFIG_DIR" ]; then
    echo -e "${YELLOW}⚠️  Config directory not found. Running setup...${NC}"
    bash "$SCRIPT_DIR/setup_dev_environment.sh"
fi

# Ensure configuration.yaml exists
if [ ! -f "$CONFIG_DIR/configuration.yaml" ]; then
    echo -e "${YELLOW}⚠️  Creating default configuration.yaml...${NC}"
    cat > "$CONFIG_DIR/configuration.yaml" << 'EOF'
# Home Assistant Development Configuration
homeassistant:
  name: Stremio Dev
  latitude: 52.3676
  longitude: 4.9041
  elevation: 0
  unit_system: metric
  time_zone: UTC
  currency: EUR

# Enable debug logging for the integration
logger:
  default: info
  logs:
    custom_components.stremio: debug
    homeassistant.components.websocket_api: warning

# Enable frontend
frontend:

# HTTP settings
http:
  server_port: 8123
EOF
fi

# Build command - use python -m for cross-platform compatibility
HA_CMD="python -m homeassistant -c $CONFIG_DIR"

if [ "$VERBOSE" = true ]; then
    HA_CMD="$HA_CMD --verbose"
fi

echo -e "${GREEN}✅ Configuration directory: ${CYAN}$CONFIG_DIR${NC}"
echo -e "${GREEN}✅ Virtual environment: ${CYAN}$VENV_PATH${NC}"
echo ""

if [ "$BACKGROUND" = true ]; then
    echo -e "${BLUE}➡️  Starting Home Assistant in background...${NC}"
    nohup $HA_CMD > "$PROJECT_ROOT/homeassistant.log" 2>&1 &
    HA_PID=$!
    echo $HA_PID > "$PROJECT_ROOT/.ha_pid"
    
    echo ""
    echo -e "${GREEN}✅ Home Assistant started with PID: $HA_PID${NC}"
    echo -e "   Logs: ${CYAN}$PROJECT_ROOT/homeassistant.log${NC}"
    echo -e "   To stop: ${YELLOW}kill $HA_PID${NC}"
else
    echo -e "${BLUE}➡️  Starting Home Assistant...${NC}"
    echo ""
fi

echo -e "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "  ${GREEN}Home Assistant will be available at:${NC}"
echo -e "  ${CYAN}http://localhost:8123${NC}"
echo -e "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ "$BACKGROUND" = false ]; then
    echo -e "${YELLOW}Press Ctrl+C to stop Home Assistant${NC}"
    echo ""
    
    # Run Home Assistant
    exec $HA_CMD
fi
