# Stremio Events

The Stremio integration fires events that you can use in automations to react to playback changes, library updates, and new content alerts.

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

### stremio_new_episodes_detected

Fired when series in your continue watching list have new episodes available. This is detected when the most recent episode number increases for a series you've been watching.

**Event Data:**
| Field | Type | Description |
|-------|------|-------------|
| `series_count` | int | Number of series with new episodes |
| `series` | array | List of series with new episodes |

**Series Item Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `imdb_id` | string | IMDB ID of the series |
| `title` | string | Title of the series |
| `previous_season` | int | Previously tracked season number |
| `previous_episode` | int | Previously tracked episode number |
| `new_season` | int | New season number |
| `new_episode` | int | New episode number |
| `episode_title` | string | Title of the new episode (if available) |
| `poster` | string | URL of the series poster |

**Example Automation:**
```yaml
automation:
  - alias: "New Episode Alert"
    trigger:
      - platform: event
        event_type: stremio_new_episodes_detected
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "📺 New Episodes Available!"
          message: >
            {% set series = trigger.event.data.series %}
            {% for show in series %}
            {{ show.title }}: S{{ '%02d' % show.new_season }}E{{ '%02d' % show.new_episode }}
            {% if show.episode_title %} - {{ show.episode_title }}{% endif %}
            {% endfor %}
          data:
            image: "{{ trigger.event.data.series[0].poster }}"
            actions:
              - action: OPEN_STREMIO
                title: "Watch Now"
```

### stremio_resume_available

Fired when there's content available to resume watching. This event is fired on every coordinator update when resumable content exists (progress between 1% and 95%), allowing you to combine it with other triggers like device power-on events.

**Event Data:**
| Field | Type | Description |
|-------|------|-------------|
| `media_id` | string | IMDB ID of the media |
| `title` | string | Title of the media |
| `type` | string | Type of media (`movie` or `series`) |
| `progress_percent` | float | Current progress percentage |
| `time_offset` | int | Position in seconds to resume from |
| `duration` | int | Total duration in seconds |
| `remaining_minutes` | int | Approximate remaining time in minutes |
| `poster` | string | URL of the media poster |
| `season` | int | Season number (series only) |
| `episode` | int | Episode number (series only) |
| `episode_title` | string | Episode title (series only) |

**Example Automation - Auto Resume on Apple TV:**
```yaml
automation:
  - alias: "Offer Resume on Apple TV Power On"
    trigger:
      - platform: state
        entity_id: media_player.apple_tv_living_room
        from: "off"
        to: "idle"
    condition:
      - condition: state
        entity_id: binary_sensor.stremio_has_continue_watching
        state: "on"
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "📺 Continue Watching?"
          message: >
            Resume {{ state_attr('sensor.stremio_continue_watching', 'items')[0].title }}?
            {{ state_attr('sensor.stremio_continue_watching', 'items')[0].progress_percent | round(0) }}% complete
          data:
            actions:
              - action: RESUME_PLAYBACK
                title: "Resume"
              - action: DISMISS
                title: "Not Now"

  - alias: "Handle Resume Playback Action"
    trigger:
      - platform: event
        event_type: mobile_app_notification_action
        event_data:
          action: RESUME_PLAYBACK
    action:
      - service: stremio.handover_to_apple_tv
        data:
          device_name: "Apple TV Living Room"
          media_id: "{{ state_attr('sensor.stremio_continue_watching', 'items')[0].imdb_id }}"
          resume: true
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
- **New episodes events** are detected when the episode number increases for tracked series
- **Resume available events** fire on every update when resumable content exists
- Events are not real-time due to API polling limitations

## Best Practices

1. **Use conditions** to prevent repeated triggers during the same viewing session
2. **Combine with sensors** for more reliable automation logic
3. **Consider debouncing** if using events for lighting control
4. **Test automations** with manual event firing first
5. **Use device triggers** in combination with Stremio events for device-specific automations

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

## Common Automation Patterns

### Pattern 1: New Episode Notification with Rich Media
```yaml
automation:
  - alias: "Rich New Episode Notification"
    trigger:
      - platform: event
        event_type: stremio_new_episodes_detected
    action:
      - repeat:
          for_each: "{{ trigger.event.data.series }}"
          sequence:
            - service: notify.mobile_app_your_phone
              data:
                title: "New Episode: {{ repeat.item.title }}"
                message: "S{{ '%02d' % repeat.item.new_season }}E{{ '%02d' % repeat.item.new_episode }}{% if repeat.item.episode_title %} - {{ repeat.item.episode_title }}{% endif %}"
                data:
                  image: "{{ repeat.item.poster }}"
```

### Pattern 2: Smart Resume Offer Based on Time of Day
```yaml
automation:
  - alias: "Evening Resume Offer"
    trigger:
      - platform: state
        entity_id: media_player.apple_tv_living_room
        to: "idle"
    condition:
      - condition: time
        after: "18:00:00"
        before: "23:00:00"
      - condition: state
        entity_id: binary_sensor.stremio_has_continue_watching
        state: "on"
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "🎬 Movie Night?"
          message: "Your Apple TV is ready. Continue where you left off?"
```

### Pattern 3: Weekly Viewing Summary
```yaml
automation:
  - alias: "Weekly Viewing Summary"
    trigger:
      - platform: time
        at: "20:00:00"
    condition:
      - condition: time
        weekday:
          - sun
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "📊 Weekly Stremio Summary"
          message: >
            This week you watched:
            - Library: {{ states('sensor.stremio_library_count') }} items
            - Continue watching: {{ state_attr('binary_sensor.stremio_has_continue_watching', 'count') }} shows
```
