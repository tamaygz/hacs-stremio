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

## Constants

See [const.py](../custom_components/stremio/const.py) for all constant definitions.
