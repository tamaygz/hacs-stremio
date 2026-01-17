#!/usr/bin/env bash
# Validate Stremio Integration - Wrapper for Python validation script
# This script calls the cross-platform Python validator

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Find Python
if command -v python &> /dev/null; then
    PYTHON_CMD="python"
elif command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
else
    echo "❌ Python not found"
    exit 1
fi

exec $PYTHON_CMD "$SCRIPT_DIR/validate_integration.py" "$@"
