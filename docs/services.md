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

### stremio.browse_catalog

Browse the Stremio catalog for popular or new movies/series with optional genre filtering.

**Parameters:**
- `media_type` (optional): "movie" or "series" (default: "movie")
- `catalog_type` (optional): "popular", "new", or "genre" (default: "popular")
- `genre` (optional): Genre filter (Action, Drama, Comedy, etc.)
- `skip` (optional): Number of items to skip for pagination (default: 0)
- `limit` (optional): Maximum items to return, 1-100 (default: 50)

**Returns:**
- `items`: List of catalog items with metadata
- `count`: Number of items returned
- `media_type`: The media type that was browsed
- `catalog_type`: The catalog type that was browsed
- `genre`: The genre filter applied (if any)

**Examples:**

Browse popular movies:
```yaml
service: stremio.browse_catalog
data:
  media_type: "movie"
  catalog_type: "popular"
  limit: 20
```

Browse action movies:
```yaml
service: stremio.browse_catalog
data:
  media_type: "movie"
  genre: "Action"
  limit: 50
```

Browse popular TV series:
```yaml
service: stremio.browse_catalog
data:
  media_type: "series"
  catalog_type: "popular"
```

Browse drama series with pagination:
```yaml
service: stremio.browse_catalog
data:
  media_type: "series"
  genre: "Drama"
  skip: 20
  limit: 20
```

### stremio.get_upcoming_episodes

Get air dates for upcoming episodes of TV series in your library. Useful for tracking when new episodes are releasing.

**Parameters:**
- `days_ahead` (optional): Number of days to look ahead, 1-30 (default: 7)

**Returns:**
- `episodes`: List of upcoming episodes with air date info
- `count`: Number of upcoming episodes found
- `days_ahead`: The days_ahead parameter used

**Each episode includes:**
- `series_id`: IMDb ID of the series
- `series_title`: Name of the series
- `poster`: Poster image URL
- `season`: Season number
- `episode`: Episode number
- `episode_title`: Title of the episode
- `air_date`: ISO format air date
- `air_date_formatted`: Human-readable date (YYYY-MM-DD)
- `days_until`: Number of days until the episode airs

**Examples:**

Get episodes airing in the next week:
```yaml
service: stremio.get_upcoming_episodes
data:
  days_ahead: 7
```

Get episodes airing in the next 2 weeks:
```yaml
service: stremio.get_upcoming_episodes
data:
  days_ahead: 14
```

**Automation example - Notify about upcoming episodes:**
```yaml
automation:
  - alias: "Notify upcoming Stremio episodes"
    trigger:
      - platform: time
        at: "09:00:00"
    action:
      - service: stremio.get_upcoming_episodes
        data:
          days_ahead: 1
        response_variable: upcoming
      - condition: template
        value_template: "{{ upcoming.count > 0 }}"
      - service: notify.mobile_app
        data:
          title: "New Episodes Today!"
          message: >
            {% for ep in upcoming.episodes %}
            {{ ep.series_title }} S{{ ep.season }}E{{ ep.episode }}
            {% endfor %}
```

### stremio.get_recommendations

Get personalized content recommendations based on your library preferences. Analyzes genres and content in your library to suggest new content you might enjoy.

**Parameters:**
- `media_type` (optional): Filter by "movie" or "series", omit for both
- `limit` (optional): Maximum recommendations, 1-50 (default: 20)

**Returns:**
- `recommendations`: List of recommended content items
- `count`: Number of recommendations
- `media_type`: The type filter applied (if any)

**Each recommendation includes:**
- `id` / `imdb_id`: Content identifier
- `title` / `name`: Content title
- `type`: "movie" or "series"
- `poster`: Poster image URL
- `year`: Release year
- `genres`: List of genres
- `recommendation_reason`: Why this was recommended (e.g., "Based on your interest in Action")

**Examples:**

Get all recommendations:
```yaml
service: stremio.get_recommendations
data:
  limit: 20
```

Get movie recommendations only:
```yaml
service: stremio.get_recommendations
data:
  media_type: "movie"
  limit: 15
```

Get TV series recommendations:
```yaml
service: stremio.get_recommendations
data:
  media_type: "series"
  limit: 10
```

### stremio.get_similar_content

Find similar movies or shows based on a specific content item. Uses genre matching and metadata to find related content.

**Parameters:**
- `media_id` (required): IMDb ID of the source content (e.g., "tt0903747")
- `limit` (optional): Maximum similar items, 1-30 (default: 10)

**Returns:**
- `similar`: List of similar content items
- `count`: Number of similar items found
- `source_media_id`: The media_id that was used as the source

**Each similar item includes:**
- `id` / `imdb_id`: Content identifier
- `title` / `name`: Content title
- `type`: "movie" or "series"
- `poster`: Poster image URL
- `year`: Release year
- `genres`: List of genres
- `similarity_score`: How similar this item is (higher is more similar)
- `similarity_reason`: Why this item is similar

**Examples:**

Find content similar to Breaking Bad:
```yaml
service: stremio.get_similar_content
data:
  media_id: "tt0903747"
  limit: 10
```

Find content similar to The Dark Knight:
```yaml
service: stremio.get_similar_content
data:
  media_id: "tt0468569"
  limit: 5
```

## Service Automation Examples

See [automations.md](guides/automations.md) for complete automation examples.
