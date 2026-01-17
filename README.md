# Stremio Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub release](https://img.shields.io/github/release/tamaygz/hacs-stremio.svg)](https://github.com/tamaygz/hacs-stremio/releases)
[![License](https://img.shields.io/github/license/tamaygz/hacs-stremio.svg)](LICENSE)

A comprehensive Home Assistant Custom Component (HACS) integration that connects to the Stremio API to track your library, viewing activity, and media consumption.

## ✨ Features

- 🎬 **Media Player Entity**: Track current playback with rich metadata
- 📊 **Multiple Sensors**: Library stats, watch time, current media, and more
- 🔔 **Events**: React to playback changes and library updates
- 📺 **Apple TV Handover**: Stream content directly to Apple TV
- 🎨 **Custom UI Cards**: Beautiful Lovelace cards for library browsing
- 🔍 **Media Source Integration**: Browse library from HA media browser
- 🎯 **Services**: Search, manage library, get stream URLs

## 📦 Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to "Integrations"
3. Click the three dots → "Custom repositories"
4. Add: `https://github.com/tamaygz/hacs-stremio`
5. Category: "Integration"
6. Search for "Stremio" and install
7. Restart Home Assistant

### Manual Installation

1. Download the latest release
2. Copy `custom_components/stremio` to your HA `custom_components` directory
3. Restart Home Assistant

## ⚙️ Configuration

1. Go to **Settings** → **Devices & Services**
2. Click **"+ Add Integration"**
3. Search for **"Stremio"**
4. Enter your Stremio credentials
5. Configure optional settings

See [Configuration Guide](docs/configuration.md) for detailed options.

## 📖 Documentation

- [Setup Guide](docs/setup.md) - Detailed installation instructions
- [Configuration](docs/configuration.md) - All configuration options
- [Services](docs/services.md) - Available services and examples
- [API Reference](docs/api.md) - Developer API documentation
- [Development Guide](docs/development.md) - Contributing and development
- [Troubleshooting](docs/troubleshooting.md) - Common issues and solutions

## 🎯 Entities

### Sensors
- Current Watching
- Last Watched
- Library Count
- Watch Time Statistics
- Continue Watching List
- And more...

### Binary Sensors
- Currently Playing
- New Content Available

### Media Player
- Read-only playback state
- Rich metadata display
- Deep link support

## 🛠️ Services

- `stremio.get_streams` - Fetch stream URLs
- `stremio.search_library` - Search your library
- `stremio.add_to_library` - Add content
- `stremio.remove_from_library` - Remove content
- `stremio.refresh_library` - Force refresh
- `stremio.handover_to_apple_tv` - Stream to Apple TV

See [Services Documentation](docs/services.md) for details and examples.

## 🚀 Quick Example

```yaml
automation:
  - alias: "Notify on new Stremio content"
    trigger:
      - platform: state
        entity_id: binary_sensor.stremio_new_content
        to: "on"
    action:
      - service: notify.mobile_app
        data:
          title: "New Content Available"
          message: "Check your Stremio library!"
```

## 🤝 Contributing

Contributions are welcome! Please read the [Development Guide](docs/development.md) first.

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linters
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Credits

- Built with [stremio-api](https://pypi.org/project/stremio-api/) Python library
- Inspired by [@AboveColin's stremio-ha](https://github.com/AboveColin/stremio-ha)

## 💬 Support

- 🐛 [Report Issues](https://github.com/tamaygz/hacs-stremio/issues)
- 💬 [Discussions](https://github.com/tamaygz/hacs-stremio/discussions)
- 📖 [Full Documentation](docs/)

## ⚠️ Disclaimer

This integration is not affiliated with, endorsed by, or connected to Stremio. Use at your own risk.

---

**Status**: 🚧 In Development | **Version**: 0.1.0