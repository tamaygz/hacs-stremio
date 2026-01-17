# VS Code Launch & Debug Configurations

This workspace includes several VS Code launch configurations for debugging Home Assistant with the Stremio integration.

## 🚀 Launch Configurations

### Home Assistant Debugging

#### 1. **Home Assistant (with HACS)** ⭐ Recommended for normal development

- Runs Home Assistant with HACS enabled
- Best for testing the full integration including HACS interactions
- Automatically restores HACS if it was disabled
- **Use when:** Developing features that interact with HACS or testing the complete setup

#### 2. **Home Assistant (without HACS)** 🎯 Best for Stremio-only debugging

- Temporarily disables HACS during the debug session
- Faster startup (HACS adds ~5-10s to boot time)
- Cleaner logs (no HACS-related messages)
- **Use when:** Debugging only the Stremio integration or when HACS causes conflicts
- **Note:** HACS is only renamed, not deleted. It's restored automatically when you run the "with HACS" config

#### 3. **Home Assistant (Verbose)**

- Runs with verbose logging for detailed output
- Shows all debug messages from all components
- **Use when:** Troubleshooting complex issues or tracing execution flow

#### 4. **Home Assistant (Skip Pip)**

- Skips automatic pip package installation
- Faster startup when dependencies are already installed
- **Use when:** You've already installed all dependencies and want quick restarts

### Test Debugging

#### 5. **Pytest: Current File**

- Runs tests in the currently open file
- **Shortcut:** Press `F5` when a test file is open

#### 6. **Pytest: All Tests**

- Runs the entire test suite
- **Use when:** Running full validation before commits

#### 7. **Pytest: All Tests with Coverage**

- Runs tests and generates coverage report
- Creates HTML report in `htmlcov/` directory
- **Use when:** Checking test coverage

#### 8. **Pytest: Config Flow Tests**

- Runs only configuration flow tests
- **Use when:** Testing integration setup/configuration

#### 9. **Pytest: Sensor Tests**

- Runs only sensor-related tests
- **Use when:** Testing sensor entities

## 🔧 VS Code Tasks

The following tasks are available (Ctrl+Shift+P → "Tasks: Run Task"):

### HACS Management

- **Disable HACS**: Temporarily disable HACS (renames folder to `.disabled`)
- **Restore HACS**: Re-enable HACS (renames back from `.disabled`)

### Development

- **Install Dependencies**: Install all development dependencies
- **Run Linter**: Run code linting checks
- **Validate Integration**: Validate integration manifest and structure
- **Clean Home Assistant Cache**: Remove cache and database (fresh start)

## 🎯 Quick Start Guide

### First Time Setup

1. Open workspace in VS Code
2. Press `Ctrl+Shift+D` to open Debug view
3. Select "Home Assistant (with HACS)" from dropdown
4. Press `F5` to start debugging

### Debugging the Stremio Integration Only

1. Select "Home Assistant (without HACS)"
2. Press `F5`
3. HACS will be temporarily disabled
4. Next time you run "with HACS", it will be restored automatically

### Running Tests

1. Open a test file (e.g., `tests/test_sensor.py`)
2. Press `F5` to run tests in that file
3. Or select "Pytest: All Tests" to run everything

## 📝 Useful Keyboard Shortcuts

- `F5` - Start debugging
- `Shift+F5` - Stop debugging
- `Ctrl+Shift+F5` - Restart debugging
- `F9` - Toggle breakpoint
- `F10` - Step over
- `F11` - Step into
- `Shift+F11` - Step out
- `Ctrl+Shift+D` - Open debug view
- `Ctrl+Shift+P` - Command palette (run tasks)

## 🔍 Breakpoint Tips

### Common Places to Set Breakpoints

**Stremio Integration:**

```python
# custom_components/stremio/__init__.py
async def async_setup_entry()  # Entry setup

# custom_components/stremio/config_flow.py
async def async_step_user()  # Config flow

# custom_components/stremio/coordinator.py
async def _async_update_data()  # Data updates

# custom_components/stremio/stremio_client.py
async def async_authenticate()  # API authentication
async def async_get_library()  # Library fetch
```

### Conditional Breakpoints

Right-click on a breakpoint → Edit Breakpoint → Add condition:

```python
# Only break for specific media_id
media_id == "tt0111161"

# Only break on errors
"error" in str(err).lower()

# Only break for specific user
user_id == "12345"
```

## 🐛 Debugging Tips

### View Home Assistant Logs

While debugging, logs appear in the integrated terminal. For real-time log viewing:

```bash
tail -f config/home-assistant.log
```

### Debug Console

Use the Debug Console (bottom panel) to execute code while paused:

```python
# Inspect variables
print(self._auth_key)
print(library_items)

# Call functions
await self.async_get_user()

# Check state
hass.states.get("sensor.stremio_library_count")
```

### Variables View

The Variables panel shows:

- **Locals**: Current function variables
- **Globals**: Module-level variables
- **self**: Object instance variables

### Watch Expressions

Add expressions to watch (right sidebar):

```python
self._auth_key
len(library_items)
hass.data[DOMAIN]
```

## 🔄 Troubleshooting

### "HACS is still loading"

If HACS was disabled but still shows in logs:

1. Run task: "Clean Home Assistant Cache"
2. Restart debug session

### "Port 8123 already in use"

Home Assistant is already running:

```bash
# Find and kill the process
ps aux | grep homeassistant
kill <PID>
```

### "Module not found"

Dependencies not installed:

1. Run task: "Install Dependencies"
2. Or manually: `pip install -r requirements_dev.txt`

### Debugging is slow

Try "Home Assistant (without HACS)" for faster startup

## 📚 Additional Resources

- [VS Code Python Debugging](https://code.visualstudio.com/docs/python/debugging)
- [Home Assistant Developer Docs](https://developers.home-assistant.io/)
- [Python Debugger (debugpy) Documentation](https://github.com/microsoft/debugpy)
