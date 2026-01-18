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

#### Polling Gate

- **Polling Gate Entities**: Select media players or other entities that control polling
  - When all selected entities are off/idle, polling is reduced to once per 24 hours
  - Leave empty to always poll at normal intervals
  - Useful for reducing API calls when not actively watching

#### Streaming Preferences

- **Default Catalog Source**: The addon to use for fetching metadata
  - Default: `cinemeta` (Stremio's default metadata addon)
  - Options: `cinemeta`, `tmdb`

- **Stream Addon Order**: Select addons in your preferred order
  - Uses a dynamic list fetched from your configured Stremio addons
  - Drag to reorder addons (your preferred order)
  - Streams from addons listed first will appear at the top
  - Leave empty to use Stremio's default order
  - New **Reset to default** checkbox: Check to clear custom order
  - Displays addon names and versions for clarity

- **Stream Quality Preference**: Preferred stream quality
  - Options: `any`, `4k`, `1080p`, `720p`, `480p`
  - Matching streams will be shown first
  - Non-matching streams are still available (sorted after matches)

#### Media Browser

- **Show Copy URL**: Show 'Copy URL' option when browsing streams
  - Default: Enabled
  - Disable to reduce clutter in the media browser

#### Apple TV Handover

- **Enable Apple TV Handover**: Allow streaming to Apple TV devices
  - Default: Disabled
  - Requires Apple TV integration

- **Apple TV Handover Method**:
  - `auto`: Automatically select best method (recommended)
  - `airplay`: Native AirPlay streaming (requires pyatv)
  - `direct`: Direct URL handover (may work for HLS streams)
  - Note: VLC deep links do NOT work on tvOS!

- **Apple TV Entity ID**: The media_player entity for direct handover
  - Example: `media_player.apple_tv_living_room`

## YAML Configuration

*This integration is configured via the UI. YAML configuration is not supported.*

## Advanced Configuration

For developers and advanced users, see [development.md](development.md).
