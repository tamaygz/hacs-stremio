# API Reference

## Stremio API Client

### StremioClient

Main client class for interacting with the Stremio API.

#### Methods

##### `async def login(email: str, password: str) -> str`

Authenticate with Stremio and retrieve auth key.

**Parameters:**
- `email`: User's email address
- `password`: User's password

**Returns:** Authentication key string

**Raises:**
- `AuthenticationError`: Invalid credentials
- `ConnectionError`: Network issues

##### `async def get_user() -> dict`

Get current user profile information.

**Returns:** User profile dictionary

##### `async def get_library() -> list`

Fetch user's library items.

**Returns:** List of library item dictionaries

##### `async def get_continue_watching(limit: int = 10) -> list`

Get continue watching list.

**Parameters:**
- `limit`: Maximum items to return

**Returns:** List of continue watching items

##### `async def get_streams(content_id: str) -> list`

Get available streams for content.

**Parameters:**
- `content_id`: Content identifier

**Returns:** List of stream dictionaries

##### `async def async_get_catalog(media_type: str = "movie", catalog_id: str = "top", genre: str | None = None, skip: int = 0, limit: int = 50) -> list`

Fetch catalog items from Cinemeta (popular, trending, etc.).

**Parameters:**
- `media_type`: Content type ("movie" or "series")
- `catalog_id`: Catalog identifier ("top" for popular/trending)
- `genre`: Optional genre filter (Action, Drama, Comedy, etc.)
- `skip`: Number of items to skip for pagination
- `limit`: Maximum items to return (default 50)

**Returns:** List of catalog item dictionaries with metadata

##### `async def async_get_popular_movies(genre: str | None = None, skip: int = 0, limit: int = 50) -> list`

Get popular movies from Cinemeta.

**Parameters:**
- `genre`: Optional genre filter
- `skip`: Number of items to skip
- `limit`: Maximum items to return

**Returns:** List of popular movie dictionaries

##### `async def async_get_popular_series(genre: str | None = None, skip: int = 0, limit: int = 50) -> list`

Get popular TV series from Cinemeta.

**Parameters:**
- `genre`: Optional genre filter
- `skip`: Number of items to skip
- `limit`: Maximum items to return

**Returns:** List of popular series dictionaries

## Supported Genres

The following 19 genres are supported for catalog filtering:
- Action, Adventure, Animation, Biography
- Comedy, Crime, Documentary, Drama
- Family, Fantasy, History, Horror
- Mystery, Romance, Sci-Fi, Sport
- Thriller, War, Western

## Coordinator

### StremioDataUpdateCoordinator

Manages data updates from Stremio API.

#### Properties

- `data`: Current cached data
- `last_update_success`: Boolean indicating last update status
- `last_update_time`: Timestamp of last update

#### Methods

##### `async def _async_update_data() -> dict`

Fetch latest data from API. Called automatically at configured intervals.

**Returns:** Dictionary with user, library, and continue watching data

##### `async def async_request_refresh() -> None`

Request an immediate data refresh from the API, bypassing the normal polling interval.

**Usage:** Called automatically after certain events (handover, library changes) or manually via the `stremio.refresh_library` service.

## API Update Behavior

### Continue Watching Refresh

The Stremio API uses an event-driven model for watch progress updates:

1. **API Backend Behavior:**
   - Stremio's backend updates watch progress when a user's viewing session syncs
   - There is no documented real-time webhook or push notification system
   - Updates happen when: playback starts, progress is made, or the app syncs with the server
   - The exact sync timing is not specified in the API documentation

2. **Integration Polling:**
   - The integration polls the Stremio API at the configured interval (default: 30 seconds)
   - This means continue watching updates may have a delay of up to the polling interval

3. **Automatic Refresh Triggers:**
   - **After handover:** When using `stremio.handover_to_apple_tv` or playing media via the media player, the integration automatically triggers a refresh after 10 seconds
   - **Library changes:** When adding/removing items, refresh is triggered immediately
   - **Gate entity activation:** When polling gate entities become active, refresh is triggered immediately
   - **Manual:** Call `stremio.refresh_library` service to force immediate refresh

4. **Why the 10-second delay?**
   - Gives Stremio's backend time to sync the watch progress
   - Balances between quick updates and avoiding unnecessary API calls
   - Based on observation that Stremio's backend typically syncs within a few seconds of playback starting

### Polling Gate Entities

Configure entities (e.g., media players) to control when polling occurs:
- When any gate entity is active: Poll at configured interval
- When all gate entities are inactive: Reduce polling to 24-hour idle interval
- Saves API calls when you're not actively using Stremio

## Constants

See [const.py](../custom_components/stremio/const.py) for all constant definitions.
