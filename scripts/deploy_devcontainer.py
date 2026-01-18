#!/usr/bin/env python3
"""
Deploy the devcontainer - Build and start the development container.
Cross-platform script that works on Windows, Linux, and macOS.
"""

import subprocess
import sys
from pathlib import Path

# Colors for terminal output
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RED = "\033[91m"
RESET = "\033[0m"

PROJECT_ROOT = Path(__file__).parent.parent


def check_docker() -> bool:
    """Check if Docker is available."""
    try:
        result = subprocess.run(
            ["docker", "--version"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            print(f"{GREEN}✅ Docker found: {result.stdout.strip()}{RESET}")
            return True
        else:
            print(f"{RED}❌ Docker not found{RESET}")
            return False
    except FileNotFoundError:
        print(f"{RED}❌ Docker not installed{RESET}")
        return False


def check_docker_running() -> bool:
    """Check if Docker daemon is running."""
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            print(f"{GREEN}✅ Docker daemon is running{RESET}")
            return True
        else:
            print(f"{RED}❌ Docker daemon is not running{RESET}")
            print(f"{YELLOW}   Please start Docker Desktop{RESET}")
            return False
    except Exception as e:
        print(f"{RED}❌ Error checking Docker: {e}{RESET}")
        return False


def build_devcontainer() -> bool:
    """Build the devcontainer image."""
    print(f"\n{BLUE}🔨 Building devcontainer image...{RESET}")
    
    try:
        # Build the container using devcontainer CLI if available
        result = subprocess.run(
            ["devcontainer", "build", "--workspace-folder", str(PROJECT_ROOT)],
            cwd=PROJECT_ROOT,
            capture_output=False,
            text=True,
            check=False,
        )
        
        if result.returncode == 0:
            print(f"{GREEN}✅ Devcontainer built successfully{RESET}")
            return True
        else:
            print(f"{RED}❌ Devcontainer build failed{RESET}")
            return False
            
    except FileNotFoundError:
        # Fallback: Use VS Code command
        print(f"{YELLOW}⚠️  devcontainer CLI not found{RESET}")
        print(f"{YELLOW}   Using VS Code to build container...{RESET}")
        print(f"{BLUE}   Please use VS Code Command Palette:{RESET}")
        print(f"{BLUE}   Ctrl+Shift+P → 'Dev Containers: Rebuild Container'{RESET}")
        return False


def start_devcontainer() -> bool:
    """Start the devcontainer."""
    print(f"\n{BLUE}🚀 Starting devcontainer...{RESET}")
    
    try:
        result = subprocess.run(
            ["devcontainer", "up", "--workspace-folder", str(PROJECT_ROOT)],
            cwd=PROJECT_ROOT,
            capture_output=False,
            text=True,
            check=False,
        )
        
        if result.returncode == 0:
            print(f"{GREEN}✅ Devcontainer started successfully{RESET}")
            return True
        else:
            print(f"{RED}❌ Devcontainer start failed{RESET}")
            return False
            
    except FileNotFoundError:
        print(f"{YELLOW}⚠️  devcontainer CLI not found{RESET}")
        print(f"{YELLOW}   Please use VS Code to start the container:{RESET}")
        print(f"{BLUE}   Ctrl+Shift+P → 'Dev Containers: Reopen in Container'{RESET}")
        return False


def main() -> int:
    """Main entry point."""
    print(f"{BLUE}🐳 Deploying Devcontainer for Stremio HACS Integration{RESET}")
    print()

    # Check Docker availability
    if not check_docker():
        print(f"\n{RED}Please install Docker Desktop:{RESET}")
        print(f"  Windows/Mac: https://www.docker.com/products/docker-desktop/")
        print(f"  Linux: https://docs.docker.com/engine/install/")
        return 1

    # Check Docker is running
    if not check_docker_running():
        return 1

    print()
    print("━" * 60)
    print(f"{BLUE}Deployment Options:{RESET}")
    print()
    print(f"{GREEN}Option 1: Using VS Code (Recommended){RESET}")
    print(f"  1. Open VS Code Command Palette (Ctrl+Shift+P)")
    print(f"  2. Run: 'Dev Containers: Reopen in Container'")
    print(f"  3. VS Code will build and start the container automatically")
    print()
    print(f"{GREEN}Option 2: Using devcontainer CLI{RESET}")
    print(f"  Install: npm install -g @devcontainers/cli")
    print(f"  Build: devcontainer build --workspace-folder .")
    print(f"  Start: devcontainer up --workspace-folder .")
    print()
    print(f"{GREEN}Option 3: Using Docker Compose (if available){RESET}")
    print(f"  docker compose -f .devcontainer/docker-compose.yml up -d")
    print("━" * 60)
    print()

    # Try to build and start if CLI is available
    print(f"{YELLOW}Attempting to use devcontainer CLI...{RESET}")
    
    if build_devcontainer():
        start_devcontainer()
        print()
        print("━" * 60)
        print(f"{GREEN}✅ Devcontainer deployment initiated{RESET}")
        print(f"{BLUE}   Access Home Assistant at: http://localhost:8123{RESET}")
        print("━" * 60)
        return 0
    else:
        print()
        print("━" * 60)
        print(f"{YELLOW}⚠️  Please use VS Code to deploy the devcontainer{RESET}")
        print("━" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
