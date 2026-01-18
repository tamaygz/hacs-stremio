# Testing Guide

This guide covers testing practices for the Stremio HACS Integration.

## Platform Requirements

> **⚠️ Important:** Tests are designed to run on **Linux/macOS** environments only.
>
> Tests will be **automatically skipped** on Windows with a descriptive message.

### Why Tests Don't Run on Windows

The `pytest-homeassistant-custom-component` package uses `pytest-socket` to block network calls during tests. This is a safety feature to ensure tests don't make real API calls. However:

- Windows uses `ProactorEventLoop` for asyncio (required by Home Assistant)
- `ProactorEventLoop` internally calls `socket.socketpair()` to create its "self-pipe"
- `pytest-socket` blocks this, causing all async tests to fail before they even start

This is a fundamental incompatibility between the Home Assistant test framework and Windows.

### Supported Testing Environments

| Environment | Status | Notes |
|-------------|--------|-------|
| **Linux (native)** | ✅ Fully supported | Recommended |
| **macOS (native)** | ✅ Fully supported | Uses SelectorEventLoop |
| **WSL2 on Windows** | ✅ Fully supported | Install dependencies in WSL |
| **Devcontainer (Docker)** | ✅ Fully supported | Best option for Windows |
| **GitHub Actions** | ✅ Fully supported | Runs on Linux runners |
| **Windows (native)** | ❌ Not supported | Tests skip automatically |

### Running Tests on Windows

**Option 1: VS Code Devcontainer (Recommended)**
1. Install Docker Desktop for Windows
2. Open project in VS Code
3. Click "Reopen in Container" when prompted
4. Run tests normally inside the container

**Option 2: WSL2**
```bash
# Open WSL terminal
wsl

# Navigate to project
cd /mnt/c/Users/YourName/path/to/hacs-stremio

# Set up Python environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements_dev.txt

# Run tests
pytest tests/
```

**Option 3: Use GitHub Actions**
Push your changes to a branch and let CI run the tests automatically.

## Running Tests

### Quick Commands

```bash
# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run specific test file
pytest tests/test_config_flow.py

# Run specific test
pytest tests/test_sensor.py::test_library_count_sensor -v

# Run with coverage
pytest tests/ --cov=custom_components/stremio --cov-report=html
```

### Using the Test Script

```bash
# Full test suite with linting
./scripts/run_tests.sh

# Tests only (skip linting)
./scripts/run_tests.sh --quick

# Auto-fix formatting
./scripts/run_tests.sh --fix

# Generate HTML coverage report
./scripts/run_tests.sh --coverage
```

### VS Code Integration

1. Open the Testing sidebar (flask icon)
2. Click "Refresh" to discover tests
3. Run all tests or individual tests
4. Use debug configurations to step through tests

---

## Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures
├── test_config_flow.py      # Configuration flow tests
├── test_coordinator.py      # Data coordinator tests
├── test_sensor.py           # Sensor entity tests
├── test_binary_sensor.py    # Binary sensor tests
├── test_media_player.py     # Media player tests
├── test_services.py         # Service call tests
└── test_init.py             # Integration setup tests
```

---

## Writing Tests

### Basic Test Structure

```python
"""Tests for the Stremio sensor platform."""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from homeassistant.core import HomeAssistant

from custom_components.stremio.sensor import StremioSensor
from custom_components.stremio.const import DOMAIN


class TestStremioSensor:
    """Test the Stremio sensor."""

    async def test_sensor_state(self, hass: HomeAssistant):
        """Test sensor returns correct state."""
        # Arrange
        coordinator = MagicMock()
        coordinator.data = {"library_count": 42}
        
        # Act
        sensor = StremioSensor(coordinator, "library_count")
        
        # Assert
        assert sensor.native_value == 42
```

### Using Fixtures

```python
# conftest.py
import pytest
from unittest.mock import MagicMock, AsyncMock

@pytest.fixture
def mock_coordinator():
    """Create a mock data coordinator."""
    coordinator = MagicMock()
    coordinator.data = {
        "library_count": 100,
        "continue_watching": [],
        "current_media": None,
    }
    coordinator.async_request_refresh = AsyncMock()
    return coordinator

@pytest.fixture
def mock_stremio_client():
    """Create a mock Stremio API client."""
    client = MagicMock()
    client.get_library = AsyncMock(return_value=[])
    client.get_user_info = AsyncMock(return_value={"email": "test@example.com"})
    return client
```

### Testing Config Flow

```python
"""Tests for config flow."""
import pytest
from unittest.mock import patch, AsyncMock

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.stremio.const import DOMAIN


async def test_form_valid_credentials(hass: HomeAssistant):
    """Test successful config flow with valid credentials."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM

    with patch(
        "custom_components.stremio.config_flow.StremioClient.login",
        return_value=True,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"email": "test@example.com", "password": "secret"},
        )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "test@example.com"
```

### Testing Async Code

```python
"""Tests for coordinator."""
import pytest
from unittest.mock import AsyncMock, patch

from custom_components.stremio.coordinator import StremioDataUpdateCoordinator


async def test_coordinator_update(hass, mock_stremio_client):
    """Test coordinator fetches data correctly."""
    with patch(
        "custom_components.stremio.coordinator.StremioClient",
        return_value=mock_stremio_client,
    ):
        coordinator = StremioDataUpdateCoordinator(
            hass, mock_stremio_client, update_interval=60
        )
        
        await coordinator.async_refresh()
        
        assert coordinator.last_update_success
        mock_stremio_client.get_library.assert_called_once()
```

---

## Mocking the Stremio API

### Creating Mock Responses

```python
# Mock library data
MOCK_LIBRARY = [
    {
        "id": "tt0111161",
        "type": "movie",
        "name": "The Shawshank Redemption",
        "poster": "https://example.com/poster.jpg",
        "year": 1994,
    },
    {
        "id": "tt0903747",
        "type": "series",
        "name": "Breaking Bad",
        "poster": "https://example.com/bb.jpg",
        "year": 2008,
    },
]

# Mock current playback
MOCK_PLAYBACK = {
    "id": "tt0111161",
    "name": "The Shawshank Redemption",
    "state": "playing",
    "progress": 0.45,
    "duration": 8520,
}

@pytest.fixture
def mock_api_responses():
    """Fixture providing mock API responses."""
    return {
        "library": MOCK_LIBRARY,
        "playback": MOCK_PLAYBACK,
    }
```

### Patching API Calls

```python
async def test_with_mock_api(hass, mock_api_responses):
    """Test integration with mocked API."""
    with patch(
        "custom_components.stremio.stremio_client.StremioClient"
    ) as mock_client_class:
        mock_client = AsyncMock()
        mock_client.get_library.return_value = mock_api_responses["library"]
        mock_client.get_playback.return_value = mock_api_responses["playback"]
        mock_client_class.return_value = mock_client
        
        # Test code that uses the client
        ...
```

---

## Coverage Requirements

- **Target:** 80% coverage on new code
- **Critical paths:** 100% coverage (config flow, error handling)

### Viewing Coverage

```bash
# Terminal report
pytest --cov=custom_components/stremio --cov-report=term-missing

# HTML report (opens in browser)
pytest --cov=custom_components/stremio --cov-report=html
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

---

## Manual Testing Checklist

### Initial Setup
- [ ] Install integration via config flow
- [ ] Verify entities are created
- [ ] Check device info appears correctly

### Sensors
- [ ] Library count updates correctly
- [ ] Continue watching count accurate
- [ ] Current media shows when playing
- [ ] Last watched updates after stopping

### Binary Sensors
- [ ] Is playing toggles correctly
- [ ] Has new content detects additions

### Media Player
- [ ] State reflects playback status
- [ ] Media info (title, poster, progress) shown
- [ ] Controls work (if applicable)

### Services
- [ ] `stremio.search_library` returns results
- [ ] `stremio.get_stream_url` provides URLs
- [ ] `stremio.refresh` triggers update

### Events
- [ ] `stremio_playback_started` fires
- [ ] `stremio_playback_stopped` fires
- [ ] `stremio_library_updated` fires on changes

### UI Cards
- [ ] Player card displays correctly
- [ ] Library card shows items
- [ ] Cards update in real-time

---

## Troubleshooting Tests

### Common Issues

**Import errors:**
```bash
# Ensure virtual environment is active
source .venv/bin/activate

# Reinstall dependencies
pip install -r requirements_dev.txt
pip install homeassistant
```

**Async test failures:**
```python
# Make sure to use async fixtures properly
@pytest.fixture
async def async_fixture():
    # Setup
    yield value
    # Teardown
```

**Mock not working:**
```python
# Patch at the point of use, not definition
# Wrong:
@patch("stremio_client.StremioClient")

# Correct:
@patch("custom_components.stremio.coordinator.StremioClient")
```

---

## CI/CD Integration

Tests run automatically on:
- Pull requests to `main`
- Pushes to `main` and `dev` branches

See `.github/workflows/test.yml` for CI configuration.
