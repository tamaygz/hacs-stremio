# Configuration Options

## Integration Options

Access via: Settings → Devices & Services → Stremio → Configure

### Available Options

#### Scan Intervals

- **Player State Update Interval**: How often to check for playback updates (30-300 seconds)
  - Default: 30 seconds
  - Lower values = more responsive, more API calls
  - Higher values = less responsive, fewer API calls

- **Library Sync Interval**: How often to sync library data (1-60 minutes)
  - Default: 5 minutes

#### Features

- **Enable Apple TV Handover**: Allow streaming to Apple TV devices
  - Default: Disabled
  - Requires Apple TV integration

- **Apple TV Handover Method**:
  - Auto: Automatically select best method
  - AirPlay: Native AirPlay streaming
  - VLC: Use VLC app on Apple TV

## YAML Configuration

*This integration is configured via the UI. YAML configuration is not supported.*

## Advanced Configuration

For developers and advanced users, see [development.md](development.md).
