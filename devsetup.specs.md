# Add Developer-Friendly Testing Environment to hacs-stremio

## Objective
Extend the hacs-stremio project to provide an easy-to-use development environment that allows developers to quickly spin up a clean Home Assistant installation with HACS pre-installed and the Stremio integration ready for testing. 

## Background
This is a Home Assistant custom integration distributed via HACS (Home Assistant Community Store). To properly test HACS-specific features and provide a realistic user experience, developers need both Home Assistant and HACS running in their development environment.

## Requirements

### 1. VS Code Devcontainer Setup
Create a `.devcontainer/` directory with the following: 

- **`devcontainer.json`**: Configure a development container that: 
  - Uses the official Home Assistant development image or appropriate Python base image
  - Exposes port 8123 for Home Assistant UI
  - Mounts the integration code into the container's `custom_components/stremio` directory
  - Sets up appropriate environment variables
  - Includes VS Code extensions for Python development, YAML, and Home Assistant
  - Defines post-create commands to set up the environment

- **`docker-compose.yml`** (if needed): 
  - Service for Home Assistant
  - Proper volume mounts for configuration and custom components
  - Network configuration for development

### 2. Setup Scripts (in `/Scripts/`)
Create the following automation scripts:

- **`setup_dev_environment.sh`**: Main setup script that:
  - Installs Home Assistant dependencies
  - Downloads and installs HACS automatically
  - Creates a basic Home Assistant configuration if none exists
  - Symlinks or copies the integration into `custom_components/`
  - Sets up a development user account
  - Provides clear status messages throughout the process

- **`install_hacs.sh`**: Standalone script to: 
  - Download the latest HACS release from GitHub
  - Extract it to the correct `custom_components/hacs` location
  - Verify the installation
  - Handle errors gracefully

- **`start_homeassistant.sh`**: Script to:
  - Start Home Assistant with appropriate flags for development
  - Show logs in real-time
  - Provide the local URL to access the UI

- **`test_integration.sh`**: Script to:
  - Run pytest tests for the integration
  - Check code quality with flake8/pylint
  - Validate Home Assistant integration manifest and structure
  - Run type checking with mypy if applicable

### 3. Documentation (in `/docs/`)
Create comprehensive developer documentation:

- **`DEVELOPMENT. md`**: Primary development guide including:
  - Prerequisites (Docker, VS Code, Git)
  - Quick start guide (3-5 steps to get running)
  - How to open the project in the devcontainer
  - How to access Home Assistant UI
  - How to add the integration via HACS custom repository
  - How to reload the integration after code changes
  - Debugging tips and tricks
  - Common issues and troubleshooting

- **`TESTING.md`**: Testing documentation: 
  - How to run automated tests
  - How to manually test the integration
  - Test coverage expectations
  - How to add new tests

- **`ARCHITECTURE.md`** (optional but recommended):
  - Overview of the integration structure
  - Key components and their responsibilities
  - Data flow diagram
  - External dependencies (Stremio API, etc.)

### 4. Configuration Files

- **`requirements_dev.txt`**: Development dependencies: 
  ```
  homeassistant>=2024.1.0
  pytest
  pytest-homeassistant-custom-component
  pytest-cov
  flake8
  pylint
  black
  mypy
  pre-commit
  ```

- **`.vscode/settings.json`**: VS Code settings for: 
  - Python path configuration
  - Linting rules
  - Formatting on save
  - Home Assistant schema validation

- **`.vscode/launch.json`**: Debug configurations for:
  - Starting Home Assistant with debugger attached
  - Running specific tests with debugger

- **`config/configuration.yaml`** (example): Minimal Home Assistant configuration for testing: 
  ```yaml
  homeassistant:
    name:  Stremio Development
    latitude: 0
    longitude: 0
    elevation: 0
    unit_system: metric
    time_zone:  UTC
  
  logger:
    default: info
    logs: 
      custom_components.stremio: debug
  ```

### 5. GitHub Workflow (optional but recommended)

- **`.github/workflows/test.yml`**: CI workflow to:
  - Run tests on pull requests
  - Validate integration structure
  - Check code quality
  - Test against multiple Home Assistant versions

### 6. Root Project Files

Update or create: 

- **`CONTRIBUTING.md`**: Contribution guidelines: 
  - How to set up the development environment (link to DEVELOPMENT.md)
  - Code style guidelines
  - How to submit PRs
  - Testing requirements

- **`README.md`**: Add a "Development" section:
  - Quick link to development setup
  - Badge for test status (if CI is set up)
  - Link to CONTRIBUTING.md

## Implementation Guidelines

### Directory Structure
After implementation, the project should look like:
```
hacs-stremio/
├── .devcontainer/
│   ├── devcontainer.json
│   └── docker-compose.yml (if needed)
├── .github/
│   └── workflows/
│       └── test. yml
├── .vscode/
│   ├── settings.json
│   └── launch.json
├── Scripts/
│   ├── setup_dev_environment.sh
│   ├── install_hacs.sh
│   ├── start_homeassistant.sh
│   └── test_integration.sh
├── docs/
│   ├── DEVELOPMENT. md
│   ├── TESTING.md
│   └── ARCHITECTURE.md
├── config/
│   └── configuration. yaml (example)
├── custom_components/
│   └── stremio/
│       └── (existing integration files)
├── tests/
│   └── (test files)
├── CONTRIBUTING.md
├── requirements_dev.txt
└── README.md (updated)
```

### Best Practices to Follow

1. **Automation First**: The setup should be as automated as possible.  A developer should be able to go from clone to running Home Assistant in < 5 minutes.

2. **Clear Error Messages**: All scripts should provide helpful error messages and suggestions when things go wrong.

3. **Idempotency**: Scripts should be safe to run multiple times without causing issues. 

4. **Documentation**: Every step should be documented.  Assume the developer has never used Home Assistant before.

5. **Cross-Platform**: Shell scripts should work on Linux, macOS, and WSL on Windows.  Use `#!/usr/bin/env bash` and avoid platform-specific commands.

6. **Security**: Don't commit any secrets, tokens, or credentials. Use environment variables or `.env` files (with `.env.example`).

7. **Version Pinning**: Pin major versions but allow minor updates (e.g., `homeassistant>=2024.1.0,<2025.0.0`).

## Testing the Implementation

After implementation, a developer should be able to: 

1. Clone the repository
2. Open in VS Code
3. Click "Reopen in Container" when prompted
4. Wait for the container to build and setup to complete
5. Open browser to `http://localhost:8123`
6. See Home Assistant running with HACS installed
7. Add the Stremio integration through HACS using a custom repository
8. Configure and test the integration

## Success Criteria

- [ ] A new developer can set up the environment in under 5 minutes
- [ ] Home Assistant starts successfully with HACS pre-installed
- [ ] The Stremio integration can be loaded and tested
- [ ] All scripts run without errors on Linux and macOS
- [ ] Documentation is clear and comprehensive
- [ ] Tests can be run easily with a single command
- [ ] The setup works in the VS Code devcontainer
- [ ] No manual Home Assistant or HACS configuration steps required (beyond initial HA onboarding)

## Notes

- The devcontainer should handle all the heavy lifting
- HACS installation should be automated (it's not in the default HA install)
- Consider using HACS 2.0 features if applicable
- Make sure the integration symlink/mount works correctly so code changes are immediately available
- Include a sample `secrets.yaml` if the integration needs API keys for Stremio