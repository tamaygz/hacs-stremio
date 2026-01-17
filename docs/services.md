# Services

## Available Services

### stremio.get_streams

Get available stream URLs for a specific content item.

**Parameters:**
- `content_id` (required): IMDb ID or content identifier
- `type` (optional): Content type ("movie" or "series")

**Example:**
```yaml
service: stremio.get_streams
data:
  content_id: "tt1234567"
  type: "movie"
```

### stremio.search_library

Search your Stremio library.

**Parameters:**
- `query` (required): Search query string

**Example:**
```yaml
service: stremio.search_library
data:
  query: "Inception"
```

### stremio.add_to_library

Add content to your Stremio library.

**Parameters:**
- `content_id` (required): Content identifier
- `type` (required): "movie" or "series"
- `name` (required): Content name

**Example:**
```yaml
service: stremio.add_to_library
data:
  content_id: "tt1234567"
  type: "movie"
  name: "Inception"
```

### stremio.remove_from_library

Remove content from your Stremio library.

**Parameters:**
- `content_id` (required): Content identifier

**Example:**
```yaml
service: stremio.remove_from_library
data:
  content_id: "tt1234567"
```

### stremio.refresh_library

Force an immediate library refresh.

**Example:**
```yaml
service: stremio.refresh_library
```

### stremio.handover_to_apple_tv

Stream content to Apple TV.

**Parameters:**
- `entity_id` (required): Apple TV media player entity
- `content_id` (optional): Content ID to play
- `stream_url` (optional): Direct stream URL
- `method` (optional): "auto", "airplay", or "vlc"

**Example:**
```yaml
service: stremio.handover_to_apple_tv
data:
  entity_id: media_player.living_room_apple_tv
  content_id: "tt1234567"
  method: "auto"
```

## Service Automation Examples

See [automations.md](guides/automations.md) for complete automation examples.
