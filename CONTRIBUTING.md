# Contributing to Stremio HACS Integration

Thank you for your interest in contributing to the Stremio HACS Integration! This document provides guidelines and information for contributors.

## Code of Conduct

Please be respectful and constructive in all interactions. We're all here to build something useful together.

## How to Contribute

### Reporting Bugs

1. **Search existing issues** to avoid duplicates
2. **Create a new issue** with:
   - Clear, descriptive title
   - Steps to reproduce
   - Expected vs actual behavior
   - Home Assistant version
   - Integration version
   - Relevant logs (with sensitive data redacted)

### Suggesting Features

1. **Check existing issues/discussions** for similar ideas
2. **Open a discussion** or issue with:
   - Clear description of the feature
   - Use case / why it's useful
   - Possible implementation approach (optional)

### Submitting Code

1. **Fork the repository**
2. **Clone your fork:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/hacs-stremio.git
   cd hacs-stremio
   ```

3. **Set up development environment:**
   ```bash
   ./scripts/setup_dev_environment.sh
   ```

4. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/issue-description
   ```

5. **Make your changes** following our code style guidelines

6. **Run tests and linting:**
   ```bash
   ./scripts/run_tests.sh
   ```

7. **Commit your changes:**
   ```bash
   git add .
   git commit -m "feat: add awesome new feature"
   ```

8. **Push to your fork:**
   ```bash
   git push origin feature/your-feature-name
   ```

9. **Open a Pull Request** against `main` branch

## Development Setup

See [docs/development.md](docs/development.md) for detailed setup instructions.

### Quick Start

```bash
# Clone and setup
git clone https://github.com/tamaygz/hacs-stremio.git
cd hacs-stremio
./scripts/setup_dev_environment.sh

# Start Home Assistant
./scripts/start_homeassistant.sh

# Run tests
./scripts/run_tests.sh
```

## Code Style Guidelines

### Python

- **Formatter:** Black (line length: 120)
- **Linter:** Flake8
- **Type hints:** Use type hints for function signatures
- **Docstrings:** Use Google-style docstrings

```python
def my_function(param1: str, param2: int = 10) -> bool:
    """Short description of function.

    Args:
        param1: Description of param1.
        param2: Description of param2.

    Returns:
        Description of return value.

    Raises:
        ValueError: When param1 is empty.
    """
    if not param1:
        raise ValueError("param1 cannot be empty")
    return len(param1) > param2
```

### Formatting

Run before committing:
```bash
black custom_components/stremio/
```

Or use `--fix` flag with test script:
```bash
./scripts/run_tests.sh --fix
```

### Import Order

1. Standard library imports
2. Third-party imports
3. Home Assistant imports
4. Local imports

```python
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN
from .coordinator import StremioDataUpdateCoordinator
```

## Commit Message Format

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
type(scope): short description

[optional body]

[optional footer]
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### Examples

```
feat(sensor): add watch time sensor

fix(config_flow): handle invalid credentials gracefully

docs: update installation instructions

test(coordinator): add tests for data refresh
```

## Testing Requirements

### Before Submitting a PR

1. **All tests pass:**
   ```bash
   pytest tests/ -v
   ```

2. **Code is formatted:**
   ```bash
   black --check custom_components/stremio/
   ```

3. **Linting passes:**
   ```bash
   flake8 custom_components/stremio/
   ```

4. **No type errors (optional but appreciated):**
   ```bash
   mypy custom_components/stremio/
   ```

### Writing Tests

- Add tests for new features
- Add regression tests for bug fixes
- Aim for >80% coverage on new code
- Use pytest fixtures for common setup

```python
import pytest
from unittest.mock import patch, MagicMock

from custom_components.stremio.sensor import StremioSensor

@pytest.fixture
def mock_coordinator():
    """Create a mock coordinator."""
    coordinator = MagicMock()
    coordinator.data = {"library_count": 42}
    return coordinator

async def test_sensor_state(mock_coordinator):
    """Test sensor returns correct state."""
    sensor = StremioSensor(mock_coordinator, "library_count")
    assert sensor.native_value == 42
```

## Pull Request Guidelines

### PR Title

Use the same format as commit messages:
```
feat(sensor): add watch time tracking
```

### PR Description

Include:
- **What** the PR does
- **Why** the change is needed
- **How** it was implemented
- Link to related issue(s)
- Screenshots (for UI changes)
- Testing instructions

### PR Checklist

- [ ] Code follows style guidelines
- [ ] Tests added/updated
- [ ] Documentation updated (if needed)
- [ ] All CI checks pass
- [ ] PR title follows conventional commit format

## Review Process

1. **Automated checks** must pass (CI)
2. **Code review** by maintainer(s)
3. **Approval** required before merge
4. **Squash merge** into main branch

## Questions?

- Open a [Discussion](https://github.com/tamaygz/hacs-stremio/discussions)
- Check existing [Issues](https://github.com/tamaygz/hacs-stremio/issues)

---

Thank you for contributing! 🎉
