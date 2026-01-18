#!/usr/bin/env python3
"""
Clean Home Assistant cache and database files.
Cross-platform script that works on Windows, Linux, and macOS.
"""

import shutil
import sys
from pathlib import Path

# Colors for terminal output
GREEN = "\033[92m"
YELLOW = "\033[93m"
RESET = "\033[0m"

PROJECT_ROOT = Path(__file__).parent.parent
STORAGE_PATH = PROJECT_ROOT / "config" / ".storage"
DB_PATTERN = "home-assistant_v2.db*"


def main() -> int:
    """Clean cache and database files."""
    cleaned = []

    # Remove .storage directory
    if STORAGE_PATH.exists():
        shutil.rmtree(STORAGE_PATH)
        cleaned.append(".storage")

    # Remove database files
    config_path = PROJECT_ROOT / "config"
    for db_file in config_path.glob(DB_PATTERN):
        db_file.unlink()
        cleaned.append(db_file.name)

    if cleaned:
        print(f"{GREEN}✅ Home Assistant cache and database cleaned{RESET}")
        print(f"{YELLOW}   Removed: {', '.join(cleaned)}{RESET}")
    else:
        print(f"{GREEN}✅ Cache already clean (nothing to remove){RESET}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
