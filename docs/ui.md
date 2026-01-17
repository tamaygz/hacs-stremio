# Stremio UI Guide - Custom Lovelace Cards

This guide covers the custom Lovelace cards provided by the Stremio integration.

## Overview

The Stremio integration includes several custom cards that are **automatically registered** when the integration loads. No manual resource registration is required.

## Available Cards

### 1. Stremio Player Card

Displays current playback status with media info and controls.

**Type:** `stremio-player-card`

#### Basic Configuration

```yaml
type: custom:stremio-player-card
entity: media_player.stremio
```

#### Full Configuration

```yaml
type: custom:stremio-player-card
entity: media_player.stremio
name: Living Room Stremio
show_progress: true
show_buttons: true
show_background: true
tap_action:
  action: more-info
```

#### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `entity` | string | Required | Media player entity ID |
| `name` | string | Entity name | Card title |
| `show_progress` | boolean | true | Show progress bar |
| `show_buttons` | boolean | true | Show control buttons |
| `show_background` | boolean | true | Show poster as background |

---

### 2. Stremio Library Card

Browse and search your Stremio library with filtering and sorting.

**Type:** `stremio-library-card`

#### Basic Configuration

```yaml
type: custom:stremio-library-card
entity: sensor.stremio_library_count
```

#### Full Configuration

```yaml
type: custom:stremio-library-card
entity: sensor.stremio_library_count
title: My Stremio Library
show_search: true
show_filters: true
max_items: 50
columns: 4
```

#### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `entity` | string | Auto-detect | Library sensor entity |
| `title` | string | "Stremio Library" | Card title |
| `show_search` | boolean | true | Show search box |
| `show_filters` | boolean | true | Show filter/sort options |
| `max_items` | number | 50 | Maximum items to display |
| `columns` | number | 4 | Grid columns (desktop) |

#### Features

- **Search**: Filter library by title as you type
- **Filters**: Filter by type (Movies, Series)
- **Sorting**: Sort by recent, title A-Z, or progress
- **Click Actions**: Click any item for details and actions
- **Lazy Loading**: Efficient loading for large libraries

---

### 3. Stremio Media Details Card

Display detailed media information with actions.

**Type:** `stremio-media-details-card`

#### Basic Configuration

```yaml
type: custom:stremio-media-details-card
entity: media_player.stremio
```

#### Full Configuration

```yaml
type: custom:stremio-media-details-card
entity: media_player.stremio
show_backdrop: true
show_cast: true
show_genres: true
max_cast: 8
```

#### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `entity` | string | Required | Media player entity |
| `show_backdrop` | boolean | true | Show blurred backdrop |
| `show_cast` | boolean | true | Show cast members |
| `show_genres` | boolean | true | Show genre tags |
| `max_cast` | number | 8 | Maximum cast to show |

---

### 4. Stremio Stream Dialog

Modal dialog for selecting streams (used by other cards).

**Type:** `stremio-stream-dialog`

This card is typically not added directly but is used by other cards when you click "Get Streams".

---

## Dashboard Examples

### Minimal Dashboard

```yaml
views:
  - title: Media
    cards:
      - type: custom:stremio-player-card
        entity: media_player.stremio
```

### Full Media Dashboard

```yaml
views:
  - title: Stremio
    cards:
      - type: vertical-stack
        cards:
          - type: custom:stremio-player-card
            entity: media_player.stremio
          - type: custom:stremio-media-details-card
            entity: media_player.stremio
      - type: custom:stremio-library-card
        title: My Library
```

### Mobile-Optimized Dashboard

```yaml
views:
  - title: Stremio
    cards:
      - type: custom:stremio-player-card
        entity: media_player.stremio
        show_background: false
      - type: custom:stremio-library-card
        columns: 2
        max_items: 20
```

---

## Styling & Theming

The cards use Home Assistant theme variables for consistent styling:

```yaml
# Example theme customization
stremio_dark:
  # Card background
  ha-card-background: "#1a1a1a"
  # Primary text
  primary-text-color: "#ffffff"
  # Secondary text
  secondary-text-color: "#aaaaaa"
  # Accent color
  primary-color: "#8458b3"  # Stremio purple
```

### CSS Variables

The cards expose these CSS variables for customization:

```css
stremio-player-card {
  --stremio-purple: #8458b3;
  --card-background: var(--ha-card-background);
  --text-primary: var(--primary-text-color);
  --text-secondary: var(--secondary-text-color);
}
```

---

## Integration with browser_mod

For popup dialogs, the cards work with [browser_mod](https://github.com/thomasloven/hass-browser_mod):

```yaml
# Show library in popup
tap_action:
  action: fire-dom-event
  browser_mod:
    service: browser_mod.popup
    data:
      content:
        type: custom:stremio-library-card
```

---

## Troubleshooting

### Cards Not Appearing

1. Clear browser cache
2. Restart Home Assistant
3. Check browser console for errors

### Card Errors

If you see "Custom element doesn't exist" errors:

1. Ensure the integration is set up
2. Check that `/local/stremio-card-bundle.js` is accessible
3. Try hard refresh (Ctrl+Shift+R)

### Styling Issues

1. Check your theme settings
2. Try a different theme
3. Report issues with screenshots

---

## See Also

- [Setup Guide](setup.md)
- [Services Guide](services.md)
- [Events Guide](events.md)
