#!/usr/bin/env python3
"""
Manage HACS integration - enable/disable for development.
Cross-platform script that works on Windows, Linux, and macOS.
"""

import shutil
import sys
from pathlib import Path

# Colors for terminal output
GREEN = "\033[92m"
RESET = "\033[0m"

PROJECT_ROOT = Path(__file__).parent.parent
HACS_PATH = PROJECT_ROOT / "config" / "custom_components" / "hacs"
HACS_DISABLED_PATH = PROJECT_ROOT / "config" / "custom_components" / "hacs.disabled"


def disable_hacs() -> int:
    """Disable HACS by renaming the directory."""
    if HACS_PATH.exists():
        shutil.move(str(HACS_PATH), str(HACS_DISABLED_PATH))
        print(f"{GREEN}✅ HACS disabled (renamed to hacs.disabled){RESET}")
    else:
        print(f"{GREEN}✅ HACS already disabled{RESET}")
    return 0


def restore_hacs() -> int:
    """Restore HACS by renaming the directory back."""
    if HACS_DISABLED_PATH.exists():
        shutil.move(str(HACS_DISABLED_PATH), str(HACS_PATH))
        print(f"{GREEN}✅ HACS restored (renamed from hacs.disabled){RESET}")
    else:
        print(f"{GREEN}✅ HACS already enabled{RESET}")
    return 0


def main() -> int:
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python manage_hacs.py [disable|restore]")
        return 1

    action = sys.argv[1].lower()

    if action == "disable":
        return disable_hacs()
    elif action == "restore":
        return restore_hacs()
    else:
        print(f"Unknown action: {action}")
        print("Usage: python manage_hacs.py [disable|restore]")
        return 1


if __name__ == "__main__":
    sys.exit(main())
