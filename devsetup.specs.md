# Developer-Friendly Testing Environment for hacs-stremio

## Objective
Provide an easy-to-use development environment that allows developers to quickly spin up a clean Home Assistant installation with HACS pre-installed and the Stremio integration ready for testing.

## Background
This is a Home Assistant custom integration distributed via HACS (Home Assistant Community Store). To properly test HACS-specific features and provide a realistic user experience, developers need both Home Assistant and HACS running in their development environment.

---

## Current Project State

### ✅ Already Implemented
- `requirements_dev.txt` - Development dependencies (pytest, black, flake8, pylint, mypy, pre-commit)
- `.vscode/settings.json` - Python, testing, and formatting configuration
- `.vscode/launch.json` - Debug configurations for HA and pytest
- `.github/workflows/test.yml` - CI with linting, tests, HACS validation, hassfest
- `.github/workflows/release.yml` - Automated release workflow
- `docs/development.md` - Comprehensive development guide
- `docs/testing.md` - Testing documentation
- `docs/architecture.md` - Architecture overview
- `.pre-commit-config.yaml` - Pre-commit hooks
- `pytest.ini` - Pytest configuration
- `tests/` - Unit test suite
- `README.md` - Project documentation with development section
- `.devcontainer/devcontainer.json` - VS Code devcontainer configuration
- `scripts/setup_dev_environment.sh` - Main setup script
- `scripts/install_hacs.sh` - HACS installation script
- `scripts/start_homeassistant.sh` - Start HA development server
- `scripts/run_tests.sh` - Comprehensive test runner
- `scripts/validate_integration.sh` - Integration validation
- `config/configuration.yaml` - Example Home Assistant configuration
- `config/secrets.yaml.example` - Secrets template
- `.env.example` - Environment variables template
- `CONTRIBUTING.md` - Contribution guidelines

### 🔲 To Be Verified
- Test the devcontainer setup end-to-end
- Verify HACS installation script on fresh environment
- Validate full developer onboarding flow (<5 min target)

---

## Requirements

### 1. VS Code Devcontainer Setup (`.devcontainer/`)

#### `devcontainer.json`
Configure a development container that:
- Uses `mcr.microsoft.com/devcontainers/python:3.11` as base image
- Exposes port 8123 for Home Assistant UI
- Mounts the integration code into the container's `custom_components/stremio` directory
- Sets up appropriate environment variables
- Includes VS Code extensions:
  - `ms-python.python`
  - `ms-python.vscode-pylance`
  - `redhat.vscode-yaml`
  - `keesschollaart.vscode-home-assistant`
- Defines `postCreateCommand` to run `scripts/setup_dev_environment.sh`
- Configures Python interpreter and testing settings

#### `docker-compose.yml` (optional)
Only if multi-service setup needed:
- Home Assistant service
- Proper volume mounts for configuration and custom components
- Network configuration for development

### 2. Setup Scripts (`/scripts/`)

> **Note**: Use lowercase `scripts/` directory (not `Scripts/`) for cross-platform compatibility.

#### `setup_dev_environment.sh`
Main setup script that:
- Checks for required dependencies (Python 3.11+, pip)
- Creates virtual environment if not exists
- Installs development dependencies from `requirements_dev.txt`
- Downloads and installs HACS automatically (calls `install_hacs.sh`)
- Creates basic Home Assistant configuration in `config/` if none exists
- Symlinks the integration into `config/custom_components/stremio`
- Installs pre-commit hooks
- Provides clear status messages with colors/emojis

#### `install_hacs.sh`
Standalone HACS installation script:
- Downloads the latest HACS release from GitHub API
- Extracts to `config/custom_components/hacs/`
- Verifies installation by checking manifest.json
- Handles errors gracefully with rollback

#### `start_homeassistant.sh`
Development server script:
- Creates config directory structure if needed
- Starts Home Assistant with `hass -c ./config --debug`
- Optionally runs in background with log tailing
- Displays the local URL (`http://localhost:8123`)
- Supports `--background` flag for headless operation

#### `run_tests.sh`
Comprehensive test runner:
- Runs pytest with coverage: `pytest tests/ --cov=custom_components/stremio`
- Runs black (format check): `black --check custom_components/stremio`
- Runs flake8 (lint): `flake8 custom_components/stremio --max-line-length=120`
- Runs mypy (type check): `mypy custom_components/stremio`
- Supports flags: `--fix` (auto-format), `--quick` (tests only)
- Exit codes indicate pass/fail for CI usage

#### `validate_integration.sh`
Integration validation script:
- Validates `manifest.json` structure
- Checks HACS compatibility (`hacs.json`)
- Runs hassfest locally if available
- Validates translations structure
- Checks for common issues

### 3. Documentation (`/docs/`)

> **Note**: Use lowercase filenames to match existing docs structure.

#### Update `development.md`
Expand existing guide to include:
- **Prerequisites**: Docker, VS Code with Dev Containers extension, Git
- **Quick Start (Devcontainer)**:
  1. Clone repo
  2. Open in VS Code
  3. Click "Reopen in Container"
  4. Wait for setup (~2 min)
  5. Run `scripts/start_homeassistant.sh`
  6. Open `http://localhost:8123`
- **Quick Start (Local)**:
  1. Clone repo
  2. Run `scripts/setup_dev_environment.sh`
  3. Run `scripts/start_homeassistant.sh`
- **Reloading After Changes**: How to use Developer Tools → YAML → Reload
- **Debugging**: Using VS Code debugger with launch.json
- **Common Issues**: Troubleshooting section

#### Create `testing.md`
Testing documentation:
- Running all tests: `pytest tests/`
- Running specific tests: `pytest tests/test_config_flow.py -v`
- Coverage reports: `pytest --cov=custom_components/stremio --cov-report=html`
- Manual testing checklist
- Writing new tests guide
- Mocking the Stremio API

#### Create `architecture.md`
Architecture overview:
- Component diagram (ASCII or Mermaid)
- Data flow: API → Coordinator → Entities → UI
- Key files and responsibilities
- Event system overview
- Frontend card architecture

### 4. Configuration Files

#### `.vscode/settings.json` (Update)
Expand existing settings:
```json
{
    "python.testing.pytestArgs": ["tests"],
    "python.testing.unittestEnabled": false,
    "python.testing.pytestEnabled": true,
    "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
    "python.formatting.provider": "black",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": "explicit"
    },
    "[python]": {
        "editor.defaultFormatter": "ms-python.black-formatter"
    },
    "yaml.schemas": {
        "https://json.schemastore.org/hacs.json": "hacs.json"
    },
    "files.associations": {
        "*.yaml": "home-assistant"
    }
}
```

#### `.vscode/launch.json` (Create)
Debug configurations:
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Home Assistant",
            "type": "debugpy",
            "request": "launch",
            "module": "homeassistant",
            "args": ["-c", "./config", "--debug"],
            "justMyCode": false
        },
        {
            "name": "Pytest: Current File",
            "type": "debugpy",
            "request": "launch",
            "module": "pytest",
            "args": ["${file}", "-v"],
            "console": "integratedTerminal"
        },
        {
            "name": "Pytest: All Tests",
            "type": "debugpy",
            "request": "launch",
            "module": "pytest",
            "args": ["tests/", "-v"],
            "console": "integratedTerminal"
        }
    ]
}
```

#### `config/configuration.yaml` (Create)
Minimal HA config for development:
```yaml
# Home Assistant Development Configuration
# This is a minimal config for testing the Stremio integration

homeassistant:
  name: Stremio Dev
  latitude: 52.3676
  longitude: 4.9041
  elevation: 0
  unit_system: metric
  time_zone: UTC
  currency: EUR

# Enable debug logging for the integration
logger:
  default: info
  logs:
    custom_components.stremio: debug
    homeassistant.components.websocket_api: warning

# Enable frontend
frontend:
  themes: !include_dir_merge_named themes/

# Enable developer tools
lovelace:
  mode: yaml
  resources:
    - url: /local/stremio-player-card.js
      type: module
    - url: /local/stremio-library-card.js
      type: module
    - url: /local/stremio-media-details-card.js
      type: module
```

#### `config/secrets.yaml.example` (Create)
Template for secrets:
```yaml
# Copy this file to secrets.yaml and fill in your values
# DO NOT commit secrets.yaml to version control!

stremio_email: your_email@example.com
stremio_password: your_password_here
```

### 5. Root Project Files

#### `CONTRIBUTING.md` (Create)
Contribution guidelines:
- Code of conduct
- How to report bugs
- How to suggest features
- Development setup (link to docs/development.md)
- Pull request process
- Code style (Black, 120 char lines)
- Testing requirements (must pass CI)
- Commit message format

#### `.env.example` (Create)
Environment variables template:
```bash
# Optional: Stremio credentials for integration testing
STREMIO_EMAIL=
STREMIO_PASSWORD=

# Optional: Custom Home Assistant config path
HA_CONFIG_PATH=./config
```

### 6. GitHub Workflows (Already Implemented ✅)

The existing `.github/workflows/test.yml` already includes:
- Matrix testing (Python 3.11, 3.12)
- Linting (black, flake8)
- Pytest with coverage
- HACS validation
- Hassfest validation

---

## Implementation Guidelines

### Directory Structure
After implementation, the project should look like:
```
hacs-stremio/
├── .devcontainer/
│   └── devcontainer.json       ✅ created
├── .github/
│   └── workflows/
│       ├── release.yml         ✅ exists
│       └── test.yml            ✅ exists
├── .vscode/
│   ├── launch.json             ✅ created
│   └── settings.json           ✅ updated
├── config/
│   ├── automations.yaml        ✅ created
│   ├── configuration.yaml      ✅ created
│   ├── scenes.yaml             ✅ created
│   ├── scripts.yaml            ✅ created
│   ├── secrets.yaml.example    ✅ created
│   └── themes/                 ✅ created
├── custom_components/
│   └── stremio/                ✅ exists
├── docs/
│   ├── api.md                  ✅ exists
│   ├── architecture.md         ✅ created
│   ├── configuration.md        ✅ exists
│   ├── development.md          ✅ updated
│   ├── events.md               ✅ exists
│   ├── services.md             ✅ exists
│   ├── setup.md                ✅ exists
│   ├── testing.md              ✅ created
│   ├── troubleshooting.md      ✅ exists
│   └── ui.md                   ✅ exists
├── examples/                   ✅ exists
├── scripts/
│   ├── install_hacs.sh         ✅ created
│   ├── run_tests.sh            ✅ created
│   ├── setup_dev_environment.sh ✅ created
│   ├── start_homeassistant.sh  ✅ created
│   └── validate_integration.sh ✅ created
├── tests/                      ✅ exists
├── .env.example                ✅ created
├── .gitignore                  ✅ updated
├── .pre-commit-config.yaml     ✅ exists
├── CHANGELOG.md                ✅ exists
├── CONTRIBUTING.md             ✅ created
├── hacs.json                   ✅ exists
├── pytest.ini                  ✅ exists
├── README.md                   ✅ exists
└── requirements_dev.txt        ✅ exists
```

### Best Practices

1. **Automation First**: Clone to running HA in < 5 minutes
2. **Clear Error Messages**: Colored output, helpful suggestions
3. **Idempotency**: Safe to run scripts multiple times
4. **Cross-Platform**: Use `#!/usr/bin/env bash`, test on Linux/macOS/WSL
5. **Security**: Never commit secrets, use `.env` files
6. **Version Pinning**: Use ranges (`>=2025.1.0,<2026.0.0`)

---

## Testing the Implementation

After implementation, a developer should be able to:

### Devcontainer Flow (Recommended)
1. Clone the repository
2. Open in VS Code
3. Click "Reopen in Container" when prompted
4. Wait for container build and setup (~2-3 min)
5. Run `scripts/start_homeassistant.sh`
6. Open browser to `http://localhost:8123`
7. Complete HA onboarding
8. Add the Stremio integration via Settings → Integrations

### Local Development Flow
1. Clone the repository
2. Run `./scripts/setup_dev_environment.sh`
3. Run `./scripts/start_homeassistant.sh`
4. Open browser to `http://localhost:8123`
5. Complete HA onboarding
6. Add the Stremio integration via Settings → Integrations

---

## Success Criteria

- [x] `requirements_dev.txt` with all dev dependencies
- [x] `.vscode/settings.json` with pytest configuration
- [x] `.github/workflows/test.yml` with CI pipeline
- [x] `docs/development.md` with basic guide
- [x] `.pre-commit-config.yaml` for code quality
- [x] `.devcontainer/devcontainer.json` for container development
- [x] `scripts/setup_dev_environment.sh` for automated setup
- [x] `scripts/install_hacs.sh` for HACS installation
- [x] `scripts/start_homeassistant.sh` for running HA
- [x] `scripts/run_tests.sh` for test execution
- [x] `config/configuration.yaml` example config
- [x] `.vscode/launch.json` debug configurations
- [x] `CONTRIBUTING.md` contribution guidelines
- [x] `docs/testing.md` testing documentation
- [x] `docs/architecture.md` architecture overview
- [ ] New developer can set up environment in < 5 minutes
- [ ] Home Assistant starts with HACS pre-installed
- [ ] Integration can be loaded and tested

---

## Implementation Priority

1. **High Priority** (Required for dev setup):
   - `.devcontainer/devcontainer.json`
   - `scripts/setup_dev_environment.sh`
   - `scripts/install_hacs.sh`
   - `scripts/start_homeassistant.sh`
   - `config/configuration.yaml`

2. **Medium Priority** (Improves DX):
   - `.vscode/launch.json`
   - `scripts/run_tests.sh`
   - Update `docs/development.md`
   - `CONTRIBUTING.md`

3. **Low Priority** (Nice to have):
   - `docs/testing.md`
   - `docs/architecture.md`
   - `scripts/validate_integration.sh`
   - `.env.example`

---

## Notes

- The devcontainer handles all heavy lifting for containerized development
- HACS installation is automated via the official get script
- Integration is symlinked so code changes are immediately available
- Use `config/secrets.yaml` for API credentials (gitignored)
- Scripts support both interactive and CI/headless modes