Add these config options:
| **Default Catalog Source** | Choose preferred addon (Cinemeta, TMDB, etc.) | More control over metadata source | ✅ DONE |
| **ADDON Stream Listing Order** | Let the user sort the available addons in his preferred order | when showing streams, always respect this configured order | ✅ DONE |
| **Stream Quality Preference** | Prefer 4K, 1080p, 720p | Filter streams by quality | ✅ DONE |

Add these entities to our stremio devices:
| **`has_new_episodes`** | True if any series has unwatched episodes | ✅ DONE |

~~Update the Catalog related UI Cards:~~
~~- Selecting media should behave like the library cards~~
~~- details view inside the card~~
~~- in case of tvshow, dialog with season/episode selection~~
✅ DONE - Browse card now has inline detail view and episode picker for TV shows

Add these new service calls:
| **`get_upcoming_episodes`** | Get air dates for series in library | `days_ahead` (default 7) | ✅ DONE |
| **`get_recommendations`** | Get suggested content based on library | `limit`, `type` | ✅ DONE |
| **`get_similar_content`** | Get similar movies/shows | `media_id`, `limit` | ✅ DONE |

~~Update all ui cards that show media items:~~
~~- add a icon button to show similar media~~
~~- make that button configurable via ui~~
✅ DONE - Library, Continue Watching, and Browse cards have "Find Similar" button

~~Add a new ui card:~~
~~- Stremio Recommendations~~
~~- Add good level of configurability via ui~~ 
✅ DONE - New stremio-recommendations-card with full configurability 


Extend functionality so these automation scenarios are possible, also add examples & docs:
2. **"New Episode Alert"** - Notify when shows in library have new episodes
4. **"Auto-Resume on Apple TV"** - When Apple TV turns on, offer to resume last watched (offer support for different notifications with callback action, e.g. mobile app notification)


Update related docs & tests.

## 🎯 Suggestions for Device Setup / Options Flow

### Current Options (already implemented):
- Apple TV integration (credentials, identifier, handover method)
- Polling interval
- Gate entity for polling
- Show copy URL toggle

### New Config Options to Consider:

| Option | Description | Value |
|--------|-------------|-------|
| **Trakt.tv Integration** | Add Trakt API key/OAuth for sync | Enables watch history sync, ratings, lists |
| **Default Catalog Source** | Choose preferred addon (Cinemeta, TMDB, etc.) | More control over metadata source |
| **Continue Watching Threshold** | % watched to consider "in progress" | Default 5%, hide items <5% or >90% |
| **Auto-refresh on media events** | Refresh library when playback stops | Better real-time sync |
| **Stream Quality Preference** | Prefer 4K, 1080p, 720p | Filter streams by quality |
| **Audio Language Preference** | Preferred audio track language | Filter streams by language |
| **Subtitle Language** | Default subtitle language | Pass to player apps |
| **Max Streams to Fetch** | Limit streams per request | Performance optimization |
| **Watchlist Sync Interval** | Separate interval for library sync | Decouple from main polling |

---

## 🔌 New Entities to Add

### Sensors

| Sensor | Description | Attributes |
|--------|-------------|------------|
| **`watch_time_today`** | Total minutes watched today | Per-day breakdown |
| **`watch_time_week`** | Total minutes watched this week | Daily breakdown |
| **`most_watched_genre`** | User's top genre by watch time | Top 5 genres with % |
| **`unwatched_library_count`** | Items in library not yet started | List of unwatched items |
| **`new_releases_count`** | New releases in followed series | List of episodes |
| **`current_stream_quality`** | Quality of active stream | Resolution, bitrate, codec |
| **`available_addons`** | Count of configured stream addons | List of addon names |

### Binary Sensors

| Binary Sensor | Description |
|---------------|-------------|
| **`has_new_episodes`** | True if any series has unwatched episodes |
| **`stremio_server_reachable`** | Health check for Stremio server connection |

### Buttons

| Button | Description |
|--------|-------------|
| **`sync_to_trakt`** | One-click sync watch history to Trakt |
| **`mark_all_watched`** | Mark all "continue watching" items as complete |
| **`clear_watch_history`** | Reset continue watching list |
| **`refresh_addons`** | Reload stream addons configuration |

---

## ⚡ New Services/Actions to Add

### High Value Services

| Service | Description | Parameters |
|---------|-------------|------------|
| **`mark_as_watched`** | Mark item complete (removes from continue) | `media_id`, `type`, `season`, `episode` |
| **`mark_as_unwatched`** | Reset progress on item | `media_id`, `type` |
| **`get_upcoming_episodes`** | Get air dates for series in library | `days_ahead` (default 7) |
| **`get_recommendations`** | Get suggested content based on library | `limit`, `type` |
| **`get_similar_content`** | Get similar movies/shows | `media_id`, `limit` |
| **`sync_with_trakt`** | Two-way sync with Trakt.tv | `direction` (push/pull/both) |
| **`get_addon_streams`** | Get streams from specific addon only | `media_id`, `addon_id` |
| **`create_playlist`** | Create a playback queue | `items[]` |
| **`play_next_episode`** | Auto-continue to next episode | `media_id` |

### Automation-Friendly Services

| Service | Description | Use Case |
|---------|-------------|----------|
| **`export_library`** | Export library as JSON | Backup automations |
| **`import_library`** | Import from JSON | Restore/migrate |
| **`get_watch_statistics`** | Detailed viewing analytics | Dashboard widgets |

---

## 🎬 Automation Ideas to Enable

With these additions, users could create automations like:

1. **"Movie Night Mode"** - When playback starts, dim lights, close blinds, set TV input
2. **"New Episode Alert"** - Notify when shows in library have new episodes
3. **"Viewing Statistics Dashboard"** - Weekly digest of watch time by genre
4. **"Auto-Resume on Apple TV"** - When Apple TV turns on, offer to resume last watched
5. **"Trakt Sync on Completion"** - Auto-sync watched status when movie ends
6. **"Quality-Based Actions"** - Enable HDR mode on TV when 4K stream starts

---

## 🏆 Priority Recommendations

**Phase 1 (Quick Wins):**
1. Add `mark_as_watched` / `mark_as_unwatched` services
2. Add `has_new_episodes` binary sensor  
3. Add stream quality preference to config

**Phase 2 (Medium Effort):**
1. Watch statistics sensors (`watch_time_today`, `watch_time_week`)
2. `get_upcoming_episodes` service
3. `get_recommendations` / `get_similar_content` services

**Phase 3 (Trakt Integration):**
1. Trakt OAuth in config flow
2. Two-way sync service
3. Trakt lists as sources

Would you like me to implement any of these suggestions? I can start with the Phase 1 items which would add the most value with minimal complexity.