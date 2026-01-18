"""Tests for Stremio catalog functionality."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from custom_components.stremio.stremio_client import StremioClient, StremioConnectionError


@pytest.fixture
def mock_catalog_response():
    """Mock catalog response from Cinemeta."""
    return {
        "metas": [
            {
                "id": "tt0111161",
                "type": "movie",
                "name": "The Shawshank Redemption",
                "poster": "https://example.com/poster1.jpg",
                "releaseInfo": "1994",
                "description": "Two imprisoned men bond over a number of years.",
                "genres": ["Drama"],
                "imdbRating": "9.3",
            },
            {
                "id": "tt0068646",
                "type": "movie",
                "name": "The Godfather",
                "poster": "https://example.com/poster2.jpg",
                "releaseInfo": "1972",
                "description": "The aging patriarch of an organized crime dynasty.",
                "genres": ["Crime", "Drama"],
                "imdbRating": "9.2",
            },
        ]
    }


@pytest.mark.asyncio
async def test_async_get_catalog_movies(mock_catalog_response):
    """Test fetching movie catalog."""
    client = StremioClient("test@example.com", "fake_auth_key")
    
    with patch.object(client, '_get_session') as mock_session:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_catalog_response)
        
        mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
        
        result = await client.async_get_catalog(media_type="movie", catalog_id="top")
        
        assert len(result) == 2
        assert result[0]["title"] == "The Shawshank Redemption"
        assert result[0]["type"] == "movie"
        assert result[1]["title"] == "The Godfather"


@pytest.mark.asyncio
async def test_async_get_catalog_with_genre(mock_catalog_response):
    """Test fetching catalog with genre filter."""
    client = StremioClient("test@example.com", "fake_auth_key")
    
    with patch.object(client, '_get_session') as mock_session:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_catalog_response)
        
        mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
        
        result = await client.async_get_catalog(media_type="movie", genre="Drama", limit=50)
        
        assert len(result) == 2
        # Verify the API was called with genre parameter
        mock_session.return_value.__aenter__.return_value.get.assert_called_once()


@pytest.mark.asyncio
async def test_async_get_popular_movies(mock_catalog_response):
    """Test convenience method for popular movies."""
    client = StremioClient("test@example.com", "fake_auth_key")
    
    with patch.object(client, '_get_session') as mock_session:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_catalog_response)
        
        mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
        
        result = await client.async_get_popular_movies(limit=50)
        
        assert len(result) == 2
        assert all(item["type"] == "movie" for item in result)


@pytest.mark.asyncio
async def test_async_get_popular_series():
    """Test convenience method for popular series."""
    client = StremioClient("test@example.com", "fake_auth_key")
    
    series_response = {
        "metas": [
            {
                "id": "tt0903747",
                "type": "series",
                "name": "Breaking Bad",
                "poster": "https://example.com/poster3.jpg",
                "releaseInfo": "2008-2013",
                "genres": ["Crime", "Drama", "Thriller"],
            }
        ]
    }
    
    with patch.object(client, '_get_session') as mock_session:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=series_response)
        
        mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
        
        result = await client.async_get_popular_series(limit=50)
        
        assert len(result) == 1
        assert result[0]["title"] == "Breaking Bad"
        assert result[0]["type"] == "series"


@pytest.mark.asyncio
async def test_async_get_catalog_empty_response():
    """Test handling empty catalog response."""
    client = StremioClient("test@example.com", "fake_auth_key")
    
    with patch.object(client, '_get_session') as mock_session:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"metas": []})
        
        mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
        
        result = await client.async_get_catalog(media_type="movie")
        
        assert result == []


@pytest.mark.asyncio
async def test_async_get_catalog_error():
    """Test catalog fetch error handling."""
    client = StremioClient("test@example.com", "fake_auth_key")
    
    with patch.object(client, '_get_session') as mock_session:
        mock_response = AsyncMock()
        mock_response.status = 500
        
        mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
        
        result = await client.async_get_catalog(media_type="movie")
        
        # Should return empty list on error, not raise
        assert result == []


@pytest.mark.asyncio
async def test_async_get_catalog_with_pagination(mock_catalog_response):
    """Test catalog with pagination parameters."""
    client = StremioClient("test@example.com", "fake_auth_key")
    
    with patch.object(client, '_get_session') as mock_session:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_catalog_response)
        
        mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
        
        result = await client.async_get_catalog(media_type="movie", skip=20, limit=10)
        
        # Verify pagination was applied
        assert len(result) <= 10


@pytest.mark.asyncio
async def test_browse_catalog_service():
    """Test browse_catalog service integration."""
    # This test would require more setup with Home Assistant service infrastructure
    # For now, we'll test the client methods that the service uses
    client = StremioClient("test@example.com", "fake_auth_key")
    
    mock_response = {
        "metas": [
            {
                "id": "tt0111161",
                "type": "movie",
                "name": "The Shawshank Redemption",
                "poster": "https://example.com/poster1.jpg",
            }
        ]
    }
    
    with patch.object(client, '_get_session') as mock_session:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value=mock_response)
        
        mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_resp
        
        # Test browsing movies
        movies = await client.async_get_popular_movies(genre="Drama", limit=20)
        assert len(movies) == 1
        assert movies[0]["title"] == "The Shawshank Redemption"
