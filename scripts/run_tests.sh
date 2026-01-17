#!/usr/bin/env bash
# Run Tests for Stremio HACS Integration
# Comprehensive test runner with linting, type checking, and coverage

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

CHECK="✅"
CROSS="❌"
ARROW="➡️"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VENV_PATH="$PROJECT_ROOT/.venv"

# Parse arguments
QUICK=false
FIX=false
COVERAGE=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -q|--quick)
            QUICK=true
            shift
            ;;
        -f|--fix)
            FIX=true
            shift
            ;;
        -c|--coverage)
            COVERAGE=true
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
            echo "  -q, --quick      Run tests only (skip linting and type checks)"
            echo "  -f, --fix        Auto-fix formatting issues with black"
            echo "  -c, --coverage   Generate HTML coverage report"
            echo "  -v, --verbose    Verbose test output"
            echo "  -h, --help       Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0               Run all checks (lint, type check, tests)"
            echo "  $0 --quick       Run only pytest"
            echo "  $0 --fix         Format code and run tests"
            echo "  $0 --coverage    Run tests with HTML coverage report"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}🧪 Running Stremio Integration Tests${NC}"
echo ""

# Track failures
FAILURES=0

# Activate virtual environment
if [ -f "$VENV_PATH/bin/activate" ]; then
    source "$VENV_PATH/bin/activate"
elif [ -f "$VENV_PATH/Scripts/activate" ]; then
    source "$VENV_PATH/Scripts/activate"
else
    echo -e "${YELLOW}⚠️  Virtual environment not found. Using system Python.${NC}"
fi

cd "$PROJECT_ROOT"

# Run black (formatter)
if [ "$QUICK" = false ]; then
    echo -e "${BLUE}${ARROW} Running Black (code formatter)...${NC}"
    
    if [ "$FIX" = true ]; then
        if black custom_components/stremio/ tests/ 2>/dev/null; then
            echo -e "${GREEN}${CHECK} Code formatted successfully${NC}"
        else
            echo -e "${RED}${CROSS} Black formatting failed${NC}"
            ((FAILURES++))
        fi
    else
        if black --check custom_components/stremio/ tests/ 2>/dev/null; then
            echo -e "${GREEN}${CHECK} Code formatting check passed${NC}"
        else
            echo -e "${RED}${CROSS} Code formatting issues found. Run with --fix to auto-format.${NC}"
            ((FAILURES++))
        fi
    fi
    echo ""
fi

# Run flake8 (linter)
if [ "$QUICK" = false ]; then
    echo -e "${BLUE}${ARROW} Running Flake8 (linter)...${NC}"
    
    if flake8 custom_components/stremio/ --max-line-length=120 --ignore=E501,W503 2>/dev/null; then
        echo -e "${GREEN}${CHECK} Linting passed${NC}"
    else
        echo -e "${RED}${CROSS} Linting issues found${NC}"
        ((FAILURES++))
    fi
    echo ""
fi

# Run mypy (type checker) - optional, don't fail on errors
if [ "$QUICK" = false ]; then
    echo -e "${BLUE}${ARROW} Running MyPy (type checker)...${NC}"
    
    if mypy custom_components/stremio/ --ignore-missing-imports --no-error-summary 2>/dev/null; then
        echo -e "${GREEN}${CHECK} Type checking passed${NC}"
    else
        echo -e "${YELLOW}⚠️  Type checking found issues (non-blocking)${NC}"
    fi
    echo ""
fi

# Run pytest
echo -e "${BLUE}${ARROW} Running Pytest...${NC}"

PYTEST_ARGS="tests/"

if [ "$VERBOSE" = true ]; then
    PYTEST_ARGS="$PYTEST_ARGS -v"
fi

if [ "$COVERAGE" = true ]; then
    PYTEST_ARGS="$PYTEST_ARGS --cov=custom_components/stremio --cov-report=html --cov-report=term"
else
    PYTEST_ARGS="$PYTEST_ARGS --cov=custom_components/stremio --cov-report=term-missing"
fi

if pytest $PYTEST_ARGS; then
    echo -e "${GREEN}${CHECK} All tests passed${NC}"
else
    echo -e "${RED}${CROSS} Some tests failed${NC}"
    ((FAILURES++))
fi

echo ""

# Summary
echo -e "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ $FAILURES -eq 0 ]; then
    echo -e "${GREEN}${CHECK} All checks passed!${NC}"
    exit 0
else
    echo -e "${RED}${CROSS} $FAILURES check(s) failed${NC}"
    exit 1
fi
