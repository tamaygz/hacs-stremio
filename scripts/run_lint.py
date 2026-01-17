#!/usr/bin/env python3
"""
Run linting and formatting checks for the Stremio HACS Integration.

This script works on Windows, Linux, and macOS.
For running tests, use the devcontainer or WSL2 (Linux required).

Usage:
    python scripts/run_lint.py [--fix]
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

# Colors for terminal output (ANSI codes)
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"

PROJECT_ROOT = Path(__file__).parent.parent
COMPONENT_PATH = PROJECT_ROOT / "custom_components" / "stremio"
TESTS_PATH = PROJECT_ROOT / "tests"

# Use the current Python interpreter (should be from venv)
PYTHON = sys.executable


def run_command(cmd: list[str], description: str) -> bool:
    """Run a command and return True if successful."""
    print(f"{BLUE}➡️  {description}...{RESET}")
    try:
        result = subprocess.run(cmd, cwd=PROJECT_ROOT, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"{GREEN}✅ {description} passed{RESET}")
            return True
        else:
            print(f"{RED}❌ {description} failed{RESET}")
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(result.stderr)
            return False
    except FileNotFoundError:
        print(f"{YELLOW}⚠️  Command not found: {cmd[0]}{RESET}")
        return True  # Don't fail on missing optional tools


def main() -> int:
    """Run all linting checks."""
    fix_mode = "--fix" in sys.argv or "-f" in sys.argv

    print(f"{BLUE}🔍 Running Stremio Integration Linting Checks{RESET}")
    print()

    failures = 0

    # Black - code formatter
    if fix_mode:
        if not run_command(
            [PYTHON, "-m", "black", str(COMPONENT_PATH), str(TESTS_PATH)],
            "Black (formatting)",
        ):
            failures += 1
    else:
        if not run_command(
            [
                PYTHON,
                "-m",
                "black",
                "--check",
                str(COMPONENT_PATH),
                str(TESTS_PATH),
            ],
            "Black (format check)",
        ):
            failures += 1
            print(f"  {YELLOW}Run with --fix to auto-format{RESET}")

    print()

    # Flake8 - linter
    if not run_command(
        [
            PYTHON,
            "-m",
            "flake8",
            str(COMPONENT_PATH),
            "--max-line-length=120",
            "--ignore=E501,W503",
        ],
        "Flake8 (linting)",
    ):
        failures += 1

    print()

    # Ruff - fast linter (if available)
    if fix_mode:
        run_command(
            [PYTHON, "-m", "ruff", "check", "--fix", str(COMPONENT_PATH)],
            "Ruff (lint + fix)",
        )
    else:
        run_command(
            [PYTHON, "-m", "ruff", "check", str(COMPONENT_PATH)],
            "Ruff (lint check)",
        )

    print()

    # MyPy - type checker (non-blocking)
    run_command(
        [
            PYTHON,
            "-m",
            "mypy",
            str(COMPONENT_PATH),
            "--ignore-missing-imports",
            "--no-error-summary",
        ],
        "MyPy (type check - advisory)",
    )

    print()
    print("━" * 60)

    if failures == 0:
        print(f"{GREEN}✅ All checks passed!{RESET}")
        return 0
    else:
        print(f"{RED}❌ {failures} check(s) failed{RESET}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
