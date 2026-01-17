#!/usr/bin/env bash
# Setup Development Environment for Stremio HACS Integration
# This script sets up everything needed for development

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Emoji indicators
CHECK="✅"
CROSS="❌"
ARROW="➡️"
GEAR="⚙️"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}${GEAR} Setting up Stremio HACS Integration development environment...${NC}"
echo ""

# Function to print status
print_status() {
    echo -e "${GREEN}${CHECK} $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}${CROSS} $1${NC}"
}

print_step() {
    echo -e "${BLUE}${ARROW} $1${NC}"
}

# Check Python version
print_step "Checking Python version..."
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    print_error "Python not found. Please install Python 3.11 or higher."
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PYTHON_MAJOR=$($PYTHON_CMD -c 'import sys; print(sys.version_info.major)')
PYTHON_MINOR=$($PYTHON_CMD -c 'import sys; print(sys.version_info.minor)')

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 11 ]); then
    print_error "Python 3.11 or higher is required. Found: Python $PYTHON_VERSION"
    exit 1
fi
print_status "Python $PYTHON_VERSION detected"

# Create virtual environment if it doesn't exist
VENV_PATH="$PROJECT_ROOT/.venv"
if [ ! -d "$VENV_PATH" ]; then
    print_step "Creating virtual environment..."
    $PYTHON_CMD -m venv "$VENV_PATH"
    print_status "Virtual environment created at $VENV_PATH"
else
    print_status "Virtual environment already exists"
fi

# Activate virtual environment
print_step "Activating virtual environment..."
if [ -f "$VENV_PATH/bin/activate" ]; then
    source "$VENV_PATH/bin/activate"
elif [ -f "$VENV_PATH/Scripts/activate" ]; then
    source "$VENV_PATH/Scripts/activate"
else
    print_error "Could not find virtual environment activation script"
    exit 1
fi
print_status "Virtual environment activated"

# Upgrade pip
print_step "Upgrading pip..."
pip install --upgrade pip --quiet
print_status "pip upgraded"

# Install development dependencies
print_step "Installing development dependencies..."
pip install -r "$PROJECT_ROOT/requirements_dev.txt" --quiet
print_status "Development dependencies installed"

# Install Home Assistant
print_step "Installing Home Assistant..."
pip install homeassistant --quiet
print_status "Home Assistant installed"

# Create config directory structure
CONFIG_DIR="$PROJECT_ROOT/config"
print_step "Setting up Home Assistant config directory..."

mkdir -p "$CONFIG_DIR"
mkdir -p "$CONFIG_DIR/custom_components"
mkdir -p "$CONFIG_DIR/www"
mkdir -p "$CONFIG_DIR/themes"

# Copy example configuration if not exists
if [ ! -f "$CONFIG_DIR/configuration.yaml" ]; then
    if [ -f "$PROJECT_ROOT/config/configuration.yaml.example" ]; then
        cp "$PROJECT_ROOT/config/configuration.yaml.example" "$CONFIG_DIR/configuration.yaml"
    elif [ -f "$PROJECT_ROOT/config/configuration.yaml" ]; then
        print_status "configuration.yaml already exists"
    fi
fi

print_status "Config directory structure created"

# Symlink integration into custom_components
INTEGRATION_SOURCE="$PROJECT_ROOT/custom_components/stremio"
INTEGRATION_TARGET="$CONFIG_DIR/custom_components/stremio"

if [ -L "$INTEGRATION_TARGET" ]; then
    print_status "Integration symlink already exists"
elif [ -d "$INTEGRATION_TARGET" ]; then
    print_warning "Integration directory exists (not a symlink). Removing and creating symlink..."
    rm -rf "$INTEGRATION_TARGET"
    ln -s "$INTEGRATION_SOURCE" "$INTEGRATION_TARGET"
    print_status "Integration symlinked"
else
    print_step "Creating symlink for integration..."
    ln -s "$INTEGRATION_SOURCE" "$INTEGRATION_TARGET"
    print_status "Integration symlinked to config/custom_components/stremio"
fi

# Symlink www resources
WWW_SOURCE="$PROJECT_ROOT/custom_components/stremio/www"
if [ -d "$WWW_SOURCE" ]; then
    for file in "$WWW_SOURCE"/*.js; do
        if [ -f "$file" ]; then
            filename=$(basename "$file")
            target="$CONFIG_DIR/www/$filename"
            if [ ! -L "$target" ] && [ ! -f "$target" ]; then
                ln -s "$file" "$target"
            fi
        fi
    done
    print_status "Frontend resources symlinked to config/www/"
fi

# Install HACS
print_step "Installing HACS..."
bash "$SCRIPT_DIR/install_hacs.sh"

# Install pre-commit hooks if pre-commit is available
if command -v pre-commit &> /dev/null; then
    print_step "Installing pre-commit hooks..."
    cd "$PROJECT_ROOT"
    pre-commit install --quiet
    print_status "Pre-commit hooks installed"
else
    print_warning "pre-commit not found in PATH, skipping hook installation"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}${CHECK} Development environment setup complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "Next steps:"
echo -e "  1. Run ${YELLOW}scripts/start_homeassistant.sh${NC} to start Home Assistant"
echo -e "  2. Open ${BLUE}http://localhost:8123${NC} in your browser"
echo -e "  3. Complete the Home Assistant onboarding"
echo -e "  4. Add the Stremio integration via Settings → Integrations"
echo ""
echo -e "Useful commands:"
echo -e "  ${YELLOW}scripts/run_tests.sh${NC}        - Run all tests"
echo -e "  ${YELLOW}scripts/run_tests.sh --quick${NC} - Run tests only (no linting)"
echo -e "  ${YELLOW}pytest tests/ -v${NC}            - Run tests with verbose output"
echo ""
