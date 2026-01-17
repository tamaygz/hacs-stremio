#!/usr/bin/env bash
# Validate Stremio Integration
# Checks manifest, HACS compatibility, and common issues

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

CHECK="✅"
CROSS="❌"
WARN="⚠️"
ARROW="➡️"

# Get paths - use Windows paths when on Windows/WSL
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
INTEGRATION_DIR="$PROJECT_ROOT/custom_components/stremio"

# Convert WSL paths to Windows paths if needed
to_native_path() {
    local path="$1"
    if [[ "$path" == /mnt/* ]] && command -v wslpath &> /dev/null; then
        wslpath -w "$path"
    else
        echo "$path"
    fi
}

# Determine Python command
if command -v python &> /dev/null; then
    PYTHON_CMD="python"
elif command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
else
    echo -e "${RED}${CROSS} Python not found${NC}"
    exit 1
fi

echo -e "${BLUE}🔍 Validating Stremio Integration${NC}"
echo ""

ERRORS=0
WARNINGS=0

# Helper functions
pass() {
    echo -e "${GREEN}${CHECK} $1${NC}"
}

fail() {
    echo -e "${RED}${CROSS} $1${NC}"
    ((ERRORS++)) || true
}

warn() {
    echo -e "${YELLOW}${WARN} $1${NC}"
    ((WARNINGS++)) || true
}

check() {
    echo -e "${BLUE}${ARROW} $1${NC}"
}

# ============================================
# Check manifest.json
# ============================================
check "Checking manifest.json..."

MANIFEST="$INTEGRATION_DIR/manifest.json"
MANIFEST_NATIVE=$(to_native_path "$MANIFEST")
if [ ! -f "$MANIFEST" ]; then
    fail "manifest.json not found"
else
    # Check required fields using Python for cross-platform compatibility
    if $PYTHON_CMD -c "import json; d=json.load(open(r'$MANIFEST_NATIVE')); assert 'domain' in d" 2>/dev/null; then
        pass "manifest.json has domain"
    else
        fail "manifest.json missing domain"
    fi

    if $PYTHON_CMD -c "import json; d=json.load(open(r'$MANIFEST_NATIVE')); assert 'name' in d" 2>/dev/null; then
        pass "manifest.json has name"
    else
        fail "manifest.json missing name"
    fi

    if $PYTHON_CMD -c "import json; d=json.load(open(r'$MANIFEST_NATIVE')); assert 'version' in d" 2>/dev/null; then
        VERSION=$($PYTHON_CMD -c "import json; print(json.load(open(r'$MANIFEST_NATIVE')).get('version', 'unknown'))")
        pass "manifest.json has version: $VERSION"
    else
        fail "manifest.json missing version"
    fi

    if $PYTHON_CMD -c "import json; d=json.load(open(r'$MANIFEST_NATIVE')); assert 'documentation' in d" 2>/dev/null; then
        pass "manifest.json has documentation URL"
    else
        warn "manifest.json missing documentation URL"
    fi

    if $PYTHON_CMD -c "import json; d=json.load(open(r'$MANIFEST_NATIVE')); assert 'issue_tracker' in d" 2>/dev/null; then
        pass "manifest.json has issue_tracker URL"
    else
        warn "manifest.json missing issue_tracker URL"
    fi

    if $PYTHON_CMD -c "import json; d=json.load(open(r'$MANIFEST_NATIVE')); assert 'codeowners' in d" 2>/dev/null; then
        pass "manifest.json has codeowners"
    else
        warn "manifest.json missing codeowners"
    fi

    # Validate JSON syntax
    if $PYTHON_CMD -c "import json; json.load(open(r'$MANIFEST_NATIVE'))" 2>/dev/null; then
        pass "manifest.json is valid JSON"
    else
        fail "manifest.json has invalid JSON syntax"
    fi
fi

echo ""

# ============================================
# Check hacs.json
# ============================================
check "Checking hacs.json..."

HACS_JSON="$PROJECT_ROOT/hacs.json"
HACS_JSON_NATIVE=$(to_native_path "$HACS_JSON")
if [ ! -f "$HACS_JSON" ]; then
    fail "hacs.json not found (required for HACS)"
else
    # Validate JSON syntax
    if $PYTHON_CMD -c "import json; json.load(open(r'$HACS_JSON_NATIVE'))" 2>/dev/null; then
        pass "hacs.json is valid JSON"
    else
        fail "hacs.json has invalid JSON syntax"
    fi

    if $PYTHON_CMD -c "import json; d=json.load(open(r'$HACS_JSON_NATIVE')); assert 'name' in d" 2>/dev/null; then
        pass "hacs.json has name"
    else
        warn "hacs.json missing name"
    fi
fi

echo ""

# ============================================
# Check required files
# ============================================
check "Checking required integration files..."

REQUIRED_FILES=(
    "__init__.py"
    "manifest.json"
    "const.py"
    "config_flow.py"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$INTEGRATION_DIR/$file" ]; then
        pass "$file exists"
    else
        fail "$file not found"
    fi
done

echo ""

# ============================================
# Check translations
# ============================================
check "Checking translations..."

TRANSLATIONS_DIR="$INTEGRATION_DIR/translations"
TRANSLATIONS_EN="$TRANSLATIONS_DIR/en.json"
TRANSLATIONS_EN_NATIVE=$(to_native_path "$TRANSLATIONS_EN")
if [ -d "$TRANSLATIONS_DIR" ]; then
    if [ -f "$TRANSLATIONS_EN" ]; then
        if $PYTHON_CMD -c "import json; json.load(open(r'$TRANSLATIONS_EN_NATIVE'))" 2>/dev/null; then
            pass "translations/en.json is valid"
        else
            fail "translations/en.json has invalid JSON"
        fi
    else
        warn "translations/en.json not found"
    fi
else
    warn "translations directory not found"
fi

echo ""

# ============================================
# Check services.yaml
# ============================================
check "Checking services.yaml..."

SERVICES_YAML="$INTEGRATION_DIR/services.yaml"
SERVICES_YAML_NATIVE=$(to_native_path "$SERVICES_YAML")
if [ -f "$SERVICES_YAML" ]; then
    pass "services.yaml exists"

    # Basic YAML validation
    if $PYTHON_CMD -c "import yaml; yaml.safe_load(open(r'$SERVICES_YAML_NATIVE'))" 2>/dev/null; then
        pass "services.yaml is valid YAML"
    else
        fail "services.yaml has invalid YAML syntax"
    fi
else
    warn "services.yaml not found (optional)"
fi

echo ""

# ============================================
# Check Python syntax
# ============================================
check "Checking Python syntax..."

SYNTAX_ERRORS=0
for pyfile in "$INTEGRATION_DIR"/*.py; do
    if [ -f "$pyfile" ]; then
        PYFILE_NATIVE=$(to_native_path "$pyfile")
        if $PYTHON_CMD -m py_compile "$PYFILE_NATIVE" 2>/dev/null; then
            : # pass silently
        else
            fail "Syntax error in $(basename "$pyfile")"
            ((SYNTAX_ERRORS++)) || true
        fi
    fi
done

if [ $SYNTAX_ERRORS -eq 0 ]; then
    pass "All Python files have valid syntax"
fi

echo ""

# ============================================
# Check for common issues
# ============================================
check "Checking for common issues..."

# Check for print statements (should use _LOGGER)
if grep -r "print(" "$INTEGRATION_DIR"/*.py 2>/dev/null | grep -v "# noqa" | grep -v "__pycache__" > /dev/null; then
    warn "Found print() statements - consider using _LOGGER instead"
else
    pass "No print() statements found"
fi

# Check for proper async
if grep -q "async def async_setup" "$INTEGRATION_DIR/__init__.py" 2>/dev/null; then
    pass "__init__.py uses async setup functions"
else
    warn "__init__.py may be missing async setup functions"
fi

echo ""

# ============================================
# Summary
# ============================================
echo -e "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}${CHECK} All checks passed!${NC}"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}${WARN} Passed with $WARNINGS warning(s)${NC}"
    exit 0
else
    echo -e "${RED}${CROSS} Failed with $ERRORS error(s) and $WARNINGS warning(s)${NC}"
    exit 1
fi
