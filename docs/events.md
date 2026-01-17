# Stremio Events

The Stremio integration fires events that you can use in automations to react to playback changes and library updates.

## Available Events

### stremio_playback_started

Fired when Stremio starts playing new content.

**Event Data:**
| Field | Type | Description |
|-------|------|-------------|
| `media_id` | string | IMDB ID of the media (e.g., `tt0903747`) |
| `title` | string | Title of the media |
| `type` | string | Type of media (`movie` or `series`) |
| `season` | int | Season number (series only) |
| `episode` | int | Episode number (series only) |
| `progress_percent` | float | Current progress percentage |

**Example Automation:**
```yaml
automation:
  - alias: "Dim lights when watching starts"
    trigger:
      - platform: event
        event_type: stremio_playback_started
    action:
      - service: light.turn_on
        target:
          entity_id: light.living_room
        data:
          brightness_pct: 20
```

### stremio_playback_stopped

Fired when Stremio stops playing content.

**Event Data:**
| Field | Type | Description |
|-------|------|-------------|
| `media_id` | string | IMDB ID of the media |
| `title` | string | Title of the media |
| `type` | string | Type of media (`movie` or `series`) |

**Example Automation:**
```yaml
automation:
  - alias: "Restore lights when watching stops"
    trigger:
      - platform: event
        event_type: stremio_playback_stopped
    action:
      - service: light.turn_on
        target:
          entity_id: light.living_room
        data:
          brightness_pct: 100
```

### stremio_new_content

Fired when the library changes (items added or removed).

**Event Data:**
| Field | Type | Description |
|-------|------|-------------|
| `action` | string | Either `added` or `removed` |
| `count_change` | int | Number of items changed |
| `new_count` | int | New total library count |
| `media_id` | string | IMDB ID (when using service calls) |
| `media_type` | string | Type of media (when using service calls) |

**Example Automation:**
```yaml
automation:
  - alias: "Notify when new content added"
    trigger:
      - platform: event
        event_type: stremio_new_content
        event_data:
          action: added
    action:
      - service: notify.mobile_app
        data:
          message: "New content added to your Stremio library!"
```

## Using Events with Templates

You can access event data in templates:

```yaml
automation:
  - alias: "Announce what's playing"
    trigger:
      - platform: event
        event_type: stremio_playback_started
    action:
      - service: tts.speak
        target:
          entity_id: tts.google_translate_say
        data:
          message: "Now playing {{ trigger.event.data.title }}"
          media_player_entity_id: media_player.living_room
```

## Filtering Events

You can filter events based on specific conditions:

```yaml
automation:
  - alias: "Movie night mode"
    trigger:
      - platform: event
        event_type: stremio_playback_started
        event_data:
          type: movie
    action:
      - service: scene.turn_on
        target:
          entity_id: scene.movie_night
```

## Event Timing

- **Playback events** are detected during each coordinator update (default: every 30 seconds)
- **Library events** are detected when the library count changes
- Events are not real-time due to API polling limitations

## Best Practices

1. **Use conditions** to prevent repeated triggers during the same viewing session
2. **Combine with sensors** for more reliable automation logic
3. **Consider debouncing** if using events for lighting control
4. **Test automations** with manual event firing first

```yaml
# Fire a test event from Developer Tools -> Events
event_type: stremio_playback_started
event_data:
  media_id: "tt0903747"
  title: "Breaking Bad"
  type: "series"
  season: 1
  episode: 1
  progress_percent: 5.0
```
