#!/usr/bin/env python3
"""Validate Stremio Integration - Cross-platform validation script."""

import json
import os
import sys
from pathlib import Path

# Colors for terminal output
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'  # No Color

CHECK = "✅"
CROSS = "❌"
WARN = "⚠️"
ARROW = "➡️"

# Counters
errors = 0
warnings = 0


def pass_msg(msg: str) -> None:
    """Print pass message."""
    print(f"{GREEN}{CHECK} {msg}{NC}")


def fail_msg(msg: str) -> None:
    """Print fail message."""
    global errors
    print(f"{RED}{CROSS} {msg}{NC}")
    errors += 1


def warn_msg(msg: str) -> None:
    """Print warning message."""
    global warnings
    print(f"{YELLOW}{WARN} {msg}{NC}")
    warnings += 1


def check_msg(msg: str) -> None:
    """Print check message."""
    print(f"{BLUE}{ARROW} {msg}{NC}")


def main() -> int:
    """Run validation checks."""
    global errors, warnings

    # Get paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    integration_dir = project_root / "custom_components" / "stremio"

    print(f"{BLUE}🔍 Validating Stremio Integration{NC}")
    print()

    # ============================================
    # Check manifest.json
    # ============================================
    check_msg("Checking manifest.json...")

    manifest_path = integration_dir / "manifest.json"
    if not manifest_path.exists():
        fail_msg("manifest.json not found")
    else:
        try:
            with open(manifest_path, encoding='utf-8') as f:
                manifest = json.load(f)

            if "domain" in manifest:
                pass_msg("manifest.json has domain")
            else:
                fail_msg("manifest.json missing domain")

            if "name" in manifest:
                pass_msg("manifest.json has name")
            else:
                fail_msg("manifest.json missing name")

            if "version" in manifest:
                pass_msg(f"manifest.json has version: {manifest['version']}")
            else:
                fail_msg("manifest.json missing version")

            if "documentation" in manifest:
                pass_msg("manifest.json has documentation URL")
            else:
                warn_msg("manifest.json missing documentation URL")

            if "issue_tracker" in manifest:
                pass_msg("manifest.json has issue_tracker URL")
            else:
                warn_msg("manifest.json missing issue_tracker URL")

            if "codeowners" in manifest:
                pass_msg("manifest.json has codeowners")
            else:
                warn_msg("manifest.json missing codeowners")

            pass_msg("manifest.json is valid JSON")

        except json.JSONDecodeError as e:
            fail_msg(f"manifest.json has invalid JSON syntax: {e}")

    print()

    # ============================================
    # Check hacs.json
    # ============================================
    check_msg("Checking hacs.json...")

    hacs_json_path = project_root / "hacs.json"
    if not hacs_json_path.exists():
        fail_msg("hacs.json not found (required for HACS)")
    else:
        try:
            with open(hacs_json_path, encoding='utf-8') as f:
                hacs_json = json.load(f)

            pass_msg("hacs.json is valid JSON")

            if "name" in hacs_json:
                pass_msg("hacs.json has name")
            else:
                warn_msg("hacs.json missing name")

        except json.JSONDecodeError as e:
            fail_msg(f"hacs.json has invalid JSON syntax: {e}")

    print()

    # ============================================
    # Check required files
    # ============================================
    check_msg("Checking required integration files...")

    required_files = ["__init__.py", "manifest.json", "const.py", "config_flow.py"]

    for file in required_files:
        if (integration_dir / file).exists():
            pass_msg(f"{file} exists")
        else:
            fail_msg(f"{file} not found")

    print()

    # ============================================
    # Check translations
    # ============================================
    check_msg("Checking translations...")

    translations_dir = integration_dir / "translations"
    if translations_dir.is_dir():
        en_json = translations_dir / "en.json"
        if en_json.exists():
            try:
                with open(en_json, encoding='utf-8') as f:
                    json.load(f)
                pass_msg("translations/en.json is valid")
            except json.JSONDecodeError as e:
                fail_msg(f"translations/en.json has invalid JSON: {e}")
        else:
            warn_msg("translations/en.json not found")
    else:
        warn_msg("translations directory not found")

    print()

    # ============================================
    # Check services.yaml
    # ============================================
    check_msg("Checking services.yaml...")

    services_yaml = integration_dir / "services.yaml"
    if services_yaml.exists():
        pass_msg("services.yaml exists")
        try:
            import yaml
            with open(services_yaml, encoding='utf-8') as f:
                yaml.safe_load(f)
            pass_msg("services.yaml is valid YAML")
        except ImportError:
            warn_msg("PyYAML not installed, skipping YAML validation")
        except Exception as e:
            fail_msg(f"services.yaml has invalid YAML syntax: {e}")
    else:
        warn_msg("services.yaml not found (optional)")

    print()

    # ============================================
    # Check Python syntax
    # ============================================
    check_msg("Checking Python syntax...")

    import py_compile

    syntax_errors = 0
    for pyfile in integration_dir.glob("*.py"):
        try:
            py_compile.compile(str(pyfile), doraise=True)
        except py_compile.PyCompileError as e:
            fail_msg(f"Syntax error in {pyfile.name}: {e}")
            syntax_errors += 1

    if syntax_errors == 0:
        pass_msg("All Python files have valid syntax")

    print()

    # ============================================
    # Check for common issues
    # ============================================
    check_msg("Checking for common issues...")

    # Check for print statements
    has_print = False
    for pyfile in integration_dir.glob("*.py"):
        with open(pyfile, encoding='utf-8') as f:
            content = f.read()
            if "print(" in content and "# noqa" not in content:
                # Simple check - could be improved
                has_print = True
                break

    if has_print:
        warn_msg("Found print() statements - consider using _LOGGER instead")
    else:
        pass_msg("No print() statements found")

    # Check for proper async
    init_file = integration_dir / "__init__.py"
    if init_file.exists():
        with open(init_file, encoding='utf-8') as f:
            content = f.read()
            if "async def async_setup" in content:
                pass_msg("__init__.py uses async setup functions")
            else:
                warn_msg("__init__.py may be missing async setup functions")

    print()

    # ============================================
    # Summary
    # ============================================
    print("━" * 60)

    if errors == 0 and warnings == 0:
        print(f"{GREEN}{CHECK} All checks passed!{NC}")
        return 0
    elif errors == 0:
        print(f"{YELLOW}{WARN} Passed with {warnings} warning(s){NC}")
        return 0
    else:
        print(f"{RED}{CROSS} Failed with {errors} error(s) and {warnings} warning(s){NC}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
