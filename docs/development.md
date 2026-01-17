# Development Guide

This guide covers setting up a development environment for the Stremio HACS Integration.

## Prerequisites

- **Docker** (for devcontainer, recommended)
- **VS Code** with [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
- **Git**
- **Python 3.11+** (for local development without Docker)

---

## Quick Start (Recommended: Devcontainer)

The fastest way to get started is using VS Code's Dev Containers:

1. **Clone the repository:**
   ```bash
   git clone https://github.com/tamaygz/hacs-stremio.git
   cd hacs-stremio
   ```

2. **Open in VS Code:**
   ```bash
   code .
   ```

3. **Reopen in Container:**
   - VS Code will prompt: "Reopen in Container" - click it
   - Or use Command Palette: `Dev Containers: Reopen in Container`

4. **Wait for setup (~2-3 minutes):**
   - Container builds
   - Dependencies install
   - HACS downloads automatically

5. **Start Home Assistant:**
   ```bash
   ./scripts/start_homeassistant.sh
   ```

6. **Open Home Assistant:**
   - Navigate to http://localhost:8123
   - Complete the onboarding wizard
   - Add Stremio via Settings → Integrations → + Add Integration

---

## Quick Start (Local Development)

For development without Docker:

1. **Clone and enter the repository:**
   ```bash
   git clone https://github.com/tamaygz/hacs-stremio.git
   cd hacs-stremio
   ```

2. **Run the setup script:**
   ```bash
   ./scripts/setup_dev_environment.sh
   ```
   
   This script:
   - Creates a Python virtual environment
   - Installs all dependencies
   - Downloads and installs HACS
   - Symlinks the integration into the config directory
   - Installs pre-commit hooks

3. **Start Home Assistant:**
   ```bash
   ./scripts/start_homeassistant.sh
   ```

4. **Open Home Assistant:**
   - Navigate to http://localhost:8123
   - Complete the onboarding wizard
   - Add Stremio via Settings → Integrations

---

## Running Tests

### Using the Test Script (Recommended)

```bash
# Run all checks (linting, type checking, tests)
./scripts/run_tests.sh

# Run tests only (skip linting)
./scripts/run_tests.sh --quick

# Auto-fix formatting issues
./scripts/run_tests.sh --fix

# Generate HTML coverage report
./scripts/run_tests.sh --coverage
```

### Using pytest Directly

```bash
# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run specific test file
pytest tests/test_config_flow.py -v

# Run with coverage
pytest tests/ --cov=custom_components/stremio --cov-report=html
```

### Using VS Code

1. Open the Testing sidebar (flask icon)
2. Click "Run All Tests" or run individual tests
3. Use F5 with debug configurations for debugging

---

## Code Quality

### Format Code (Black)

```bash
# Check formatting
black --check custom_components/stremio/

# Auto-format
black custom_components/stremio/
```

### Lint Code (Flake8)

```bash
flake8 custom_components/stremio/ --max-line-length=120
```

### Type Check (MyPy)

```bash
mypy custom_components/stremio/ --ignore-missing-imports
```

---

## Debugging

### VS Code Debugger

The project includes debug configurations in `.vscode/launch.json`:

1. **Home Assistant**: Start HA with debugger attached
2. **Pytest: Current File**: Debug the current test file
3. **Pytest: All Tests**: Debug all tests

To debug:
1. Set breakpoints in your code
2. Press F5 or select a debug configuration
3. Step through code with F10/F11

### Debug Logging

The development config enables debug logging for the integration:

```yaml
# config/configuration.yaml
logger:
  default: info
  logs:
    custom_components.stremio: debug
```

---

## Reloading After Code Changes

### Python Changes

1. Go to **Developer Tools** → **YAML**
2. Click **Stremio** under "YAML configuration reloading"
3. Or restart Home Assistant for major changes

### Frontend Changes (Lovelace Cards)

1. Hard refresh your browser (Ctrl+Shift+R / Cmd+Shift+R)
2. Or clear browser cache

---

## Project Structure

```
hacs-stremio/
├── .devcontainer/           # VS Code devcontainer config
│   └── devcontainer.json
├── .github/workflows/       # CI/CD pipelines
│   ├── release.yml
│   └── test.yml
├── .vscode/                 # VS Code settings
│   ├── launch.json          # Debug configurations
│   └── settings.json        # Editor settings
├── config/                  # HA development config
│   ├── configuration.yaml
│   └── custom_components/   # Symlinked integration
├── custom_components/
│   └── stremio/
│       ├── __init__.py      # Integration setup
│       ├── manifest.json    # Integration metadata
│       ├── const.py         # Constants
│       ├── config_flow.py   # Configuration UI
│       ├── coordinator.py   # Data coordinator
│       ├── stremio_client.py # API client
│       ├── sensor.py        # Sensor entities
│       ├── binary_sensor.py # Binary sensor entities
│       ├── media_player.py  # Media player entity
│       ├── services.py      # Custom services
│       └── www/             # Frontend cards
├── docs/                    # Documentation
├── scripts/                 # Automation scripts
│   ├── setup_dev_environment.sh
│   ├── install_hacs.sh
│   ├── start_homeassistant.sh
│   └── run_tests.sh
├── tests/                   # Unit tests
├── requirements_dev.txt     # Development dependencies
└── README.md
```

---

## Common Issues

### "Module not found" errors

Make sure you're using the virtual environment:
```bash
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows
```

### HACS not showing in integrations

1. Restart Home Assistant completely
2. Check that HACS is in `config/custom_components/hacs/`
3. Check logs for HACS errors

### Integration not loading

1. Check `config/custom_components/stremio/` exists (symlink)
2. Check logs: `tail -f config/home-assistant.log`
3. Verify `manifest.json` has correct format

### Port 8123 already in use

```bash
# Find and kill the process
lsof -i :8123
kill <PID>
```

### Tests failing with import errors

Ensure you have all dependencies:
```bash
pip install -r requirements_dev.txt
pip install homeassistant
```

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes
4. Run tests: `./scripts/run_tests.sh`
5. Commit with descriptive message
6. Push and create a Pull Request

See [CONTRIBUTING.md](../CONTRIBUTING.md) for detailed guidelines.

---

## Useful Resources

- [Home Assistant Developer Docs](https://developers.home-assistant.io/)
- [HACS Developer Documentation](https://hacs.xyz/docs/developer/start)
- [Stremio API Documentation](https://github.com/Stremio/stremio-api-docs)
