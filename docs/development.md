# Development Guide

## Setting Up Development Environment

### Prerequisites

- Python 3.11 or higher
- Home Assistant development environment
- Git

### Initial Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/tamaygz/hacs-stremio.git
   cd hacs-stremio
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements_dev.txt
   ```

4. **Install pre-commit hooks:**
   ```bash
   pre-commit install
   ```

## Running Tests

### Unit Tests

```bash
pytest tests/
```

### With Coverage

```bash
pytest --cov=custom_components.stremio tests/
```

### Specific Test File

```bash
pytest tests/test_config_flow.py
```

## Code Quality

### Format Code

```bash
black custom_components/stremio/
```

### Lint Code

```bash
flake8 custom_components/stremio/
pylint custom_components/stremio/
```

### Type Check

```bash
mypy custom_components/stremio/
```

## Project Structure

```
custom_components/stremio/
├── __init__.py           # Integration setup
├── manifest.json         # Integration metadata
├── const.py              # Constants
├── config_flow.py        # Configuration UI
├── coordinator.py        # Data coordinator
├── stremio_client.py     # API client
├── sensor.py             # Sensor entities
├── binary_sensor.py      # Binary sensor entities
├── media_player.py       # Media player entity
└── services.py           # Custom services
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linters
5. Submit a pull request

See [contributing guidelines](https://github.com/tamaygz/hacs-stremio/blob/main/CONTRIBUTING.md) for more details.
