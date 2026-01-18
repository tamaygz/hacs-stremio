"""Tests for Stremio media source catalog browsing."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.components.media_player import MediaClass, MediaType
from custom_components.stremio.media_source import (
    StremioMediaSource,
    CATALOGS_IDENTIFIER,
    POPULAR_MOVIES_IDENTIFIER,
    POPULAR_SERIES_IDENTIFIER,
    MOVIE_GENRES_IDENTIFIER,
    SERIES_GENRES_IDENTIFIER,
)


@pytest.fixture
def mock_hass():
    """Mock Home Assistant instance."""
    hass = MagicMock()
    hass.data = {}
    return hass


@pytest.fixture
def mock_coordinator():
    """Mock coordinator with client."""
    coordinator = MagicMock()
    coordinator.client = MagicMock()
    return coordinator


@pytest.fixture
def media_source(mock_hass):
    """Create media source instance."""
    return StremioMediaSource(mock_hass)


@pytest.mark.asyncio
async def test_build_catalogs_browse(media_source):
    """Test building catalogs browse menu."""
    result = media_source._build_catalogs_browse()
    
    assert result.identifier == CATALOGS_IDENTIFIER
    assert result.title == "Browse Catalogs"
    assert result.can_expand is True
    assert len(result.children) >= 6  # At least 6 sections including genres


@pytest.mark.asyncio
async def test_build_movie_genres_browse(media_source):
    """Test building movie genres list."""
    result = media_source._build_movie_genres_browse()
    
    assert result.identifier == MOVIE_GENRES_IDENTIFIER
    assert result.title == "Movie Genres"
    assert result.media_content_type == MediaType.MOVIE
    assert len(result.children) == 19  # 19 genres


@pytest.mark.asyncio
async def test_build_series_genres_browse(media_source):
    """Test building series genres list."""
    result = media_source._build_series_genres_browse()
    
    assert result.identifier == SERIES_GENRES_IDENTIFIER
    assert result.title == "TV Show Genres"
    assert result.media_content_type == MediaType.TVSHOW
    assert len(result.children) == 19  # 19 genres


@pytest.mark.asyncio
async def test_build_genre_content_browse_movies(media_source, mock_hass, mock_coordinator):
    """Test building genre-filtered movie content."""
    # Setup mock coordinator
    mock_hass.data = {"stremio": {"test_entry": {"coordinator": mock_coordinator}}}
    
    mock_catalog_items = [
        {
            "id": "tt0111161",
            "title": "The Shawshank Redemption",
            "type": "movie",
            "poster": "https://example.com/poster.jpg",
            "year": "1994",
        }
    ]
    
    mock_coordinator.client.async_get_popular_movies = AsyncMock(return_value=mock_catalog_items)
    
    result = await media_source._build_genre_content_browse("movie_genres/Drama", "movie")
    
    assert "Drama" in result.title
    assert result.media_content_type == MediaType.MOVIE
    assert len(result.children) == 1
    mock_coordinator.client.async_get_popular_movies.assert_called_once_with(genre="Drama", limit=50)


@pytest.mark.asyncio
async def test_build_genre_content_browse_series(media_source, mock_hass, mock_coordinator):
    """Test building genre-filtered series content."""
    # Setup mock coordinator
    mock_hass.data = {"stremio": {"test_entry": {"coordinator": mock_coordinator}}}
    
    mock_catalog_items = [
        {
            "id": "tt0903747",
            "title": "Breaking Bad",
            "type": "series",
            "poster": "https://example.com/poster.jpg",
            "year": "2008",
        }
    ]
    
    mock_coordinator.client.async_get_popular_series = AsyncMock(return_value=mock_catalog_items)
    
    result = await media_source._build_genre_content_browse("series_genres/Crime", "series")
    
    assert "Crime" in result.title
    assert result.media_content_type == MediaType.TVSHOW
    assert len(result.children) == 1
    mock_coordinator.client.async_get_popular_series.assert_called_once_with(genre="Crime", limit=50)


@pytest.mark.asyncio
async def test_build_popular_movies_browse(media_source, mock_hass, mock_coordinator):
    """Test building popular movies browse."""
    # Setup mock coordinator
    mock_hass.data = {"stremio": {"test_entry": {"coordinator": mock_coordinator}}}
    
    mock_catalog_items = [
        {
            "id": "tt0111161",
            "title": "The Shawshank Redemption",
            "type": "movie",
            "poster": "https://example.com/poster.jpg",
        }
    ]
    
    mock_coordinator.client.async_get_popular_movies = AsyncMock(return_value=mock_catalog_items)
    
    result = await media_source._build_popular_movies_browse()
    
    assert result.identifier == POPULAR_MOVIES_IDENTIFIER
    assert result.title == "Popular Movies"
    assert len(result.children) == 1


@pytest.mark.asyncio
async def test_build_catalog_item_movie(media_source):
    """Test building catalog item for movie."""
    item = {
        "id": "tt0111161",
        "imdb_id": "tt0111161",
        "title": "The Shawshank Redemption",
        "type": "movie",
        "poster": "https://example.com/poster.jpg",
        "year": "1994",
    }
    
    result = media_source._build_catalog_item(item)
    
    assert result is not None
    assert result.title == "The Shawshank Redemption (1994)"
    assert result.media_class == MediaClass.MOVIE
    assert result.identifier == "movie/tt0111161"


@pytest.mark.asyncio
async def test_build_catalog_item_series(media_source):
    """Test building catalog item for series."""
    item = {
        "id": "tt0903747",
        "imdb_id": "tt0903747",
        "title": "Breaking Bad",
        "type": "series",
        "poster": "https://example.com/poster.jpg",
    }
    
    result = media_source._build_catalog_item(item)
    
    assert result is not None
    assert result.title == "Breaking Bad"
    assert result.media_class == MediaClass.TV_SHOW
    assert result.identifier == "series/tt0903747"


@pytest.mark.asyncio
async def test_build_catalog_item_invalid(media_source):
    """Test building catalog item with invalid data."""
    item = {"type": "movie"}  # Missing required fields
    
    result = media_source._build_catalog_item(item)
    
    assert result is None
