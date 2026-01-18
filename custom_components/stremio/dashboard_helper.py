"""Helper module for creating Stremio dashboards."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

_LOGGER = logging.getLogger(__name__)

DASHBOARD_URL_PATH = "stremio-testing"
DASHBOARD_TITLE = "Stremio Testing"
DASHBOARD_ICON = "mdi:filmstrip"
EVENT_LOVELACE_UPDATED = "lovelace_updated"


def get_testing_dashboard_config(entity_id: str) -> dict[str, Any]:
    """Generate a testing dashboard configuration.

    Args:
        entity_id: The entity ID of the Stremio media player

    Returns:
        Dashboard configuration dictionary
    """
    # Extract the sensor entity IDs from the media player entity ID
    # Expected format: media_player.stremio_<user_id>_stremio
    # Sensor format: sensor.stremio_<user_id>_<sensor_type>
    base_id = entity_id.replace("media_player.", "sensor.").replace("_stremio", "")

    continue_watching_sensor = f"{base_id}_continue_watching_count"
    library_sensor = f"{base_id}_library_count"

    return {
        "views": [
            {
                "title": "Home",
                "type": "sections",
                "max_columns": 2,
                "sections": [
                    # Catalog card - horizontal scroll OFF
                    {
                        "type": "grid",
                        "cards": [
                            {
                                "type": "heading",
                                "heading": "Catalog card, horizontal scroll OFF",
                                "heading_style": "title",
                            },
                            {
                                "type": "custom:stremio-browse-card",
                                "title": "Browse Stremio",
                                "default_view": "popular",
                                "default_type": "movie",
                                "show_view_controls": True,
                                "show_type_controls": True,
                                "show_genre_filter": True,
                                "show_title": True,
                                "show_rating": True,
                                "show_media_type_badge": True,
                                "show_similar_button": True,
                                "columns": 4,
                                "max_items": 50,
                                "card_height": 0,
                                "poster_aspect_ratio": "2/3",
                                "horizontal_scroll": False,
                                "tap_action": "details",
                                "grid_options": {"columns": "full"},
                            },
                        ],
                    },
                    # Catalog card - horizontal scroll ON
                    {
                        "type": "grid",
                        "cards": [
                            {
                                "type": "heading",
                                "heading": "Catalog card, horizontal scroll ON",
                                "heading_style": "title",
                            },
                            {
                                "type": "custom:stremio-browse-card",
                                "title": "Browse Stremio",
                                "default_view": "popular",
                                "default_type": "movie",
                                "show_view_controls": True,
                                "show_type_controls": True,
                                "show_genre_filter": True,
                                "show_title": True,
                                "show_rating": True,
                                "show_media_type_badge": True,
                                "show_similar_button": True,
                                "columns": 4,
                                "max_items": 50,
                                "card_height": 0,
                                "poster_aspect_ratio": "2/3",
                                "horizontal_scroll": True,
                                "tap_action": "details",
                                "grid_options": {"columns": "full"},
                            },
                        ],
                    },
                    # Continue watching card - horizontal scroll ON
                    {
                        "type": "grid",
                        "cards": [
                            {
                                "type": "heading",
                                "heading": "Continue watching card, horizontal scroll ON",
                                "heading_style": "title",
                            },
                            {
                                "type": "custom:stremio-continue-watching-card",
                                "title": "Continue Watching",
                                "show_filters": True,
                                "show_title": True,
                                "show_progress_text": True,
                                "show_media_type_badge": False,
                                "show_similar_button": True,
                                "max_items": 20,
                                "columns": 4,
                                "card_height": 0,
                                "poster_aspect_ratio": "2/3",
                                "horizontal_scroll": True,
                                "tap_action": "details",
                                "default_sort": "recent",
                                "entity": continue_watching_sensor,
                                "grid_options": {"columns": "full"},
                            },
                        ],
                    },
                    # Continue watching card - horizontal scroll OFF
                    {
                        "type": "grid",
                        "cards": [
                            {
                                "type": "heading",
                                "heading_style": "title",
                                "heading": "Continue watching card, horizontal scroll OFF",
                            },
                            {
                                "type": "custom:stremio-continue-watching-card",
                                "title": "Continue Watching",
                                "show_filters": True,
                                "show_title": True,
                                "show_progress_text": True,
                                "show_media_type_badge": False,
                                "show_similar_button": True,
                                "max_items": 20,
                                "columns": 4,
                                "card_height": 0,
                                "poster_aspect_ratio": "2/3",
                                "horizontal_scroll": False,
                                "tap_action": "details",
                                "default_sort": "recent",
                                "grid_options": {"columns": "full"},
                            },
                        ],
                    },
                    # Library card - horizontal scroll ON
                    {
                        "type": "grid",
                        "cards": [
                            {
                                "type": "heading",
                                "heading": "Library card, horizontal scroll ON",
                                "heading_style": "title",
                            },
                            {
                                "type": "custom:stremio-library-card",
                                "title": "Stremio Library",
                                "show_search": True,
                                "show_filters": True,
                                "show_title": True,
                                "max_items": 50,
                                "columns": 3,
                                "card_height": 0,
                                "entity": library_sensor,
                                "show_media_type_badge": True,
                                "grid_options": {"columns": "full"},
                                "poster_aspect_ratio": "2/3",
                                "horizontal_scroll": True,
                            },
                        ],
                    },
                    # Library card - horizontal scroll OFF
                    {
                        "type": "grid",
                        "cards": [
                            {
                                "type": "heading",
                                "heading": "Library card, horizontal scroll OFF",
                                "heading_style": "title",
                            },
                            {
                                "type": "custom:stremio-library-card",
                                "title": "Stremio Library",
                                "show_search": True,
                                "show_filters": True,
                                "show_title": True,
                                "max_items": 50,
                                "columns": 3,
                                "card_height": 0,
                                "show_similar_button": True,
                                "show_media_type_badge": True,
                                "grid_options": {"columns": "full"},
                                "poster_aspect_ratio": "2/3",
                                "tap_action": "details",
                                "default_sort": "recent",
                            },
                        ],
                    },
                    # Media details card - first instance
                    {
                        "type": "grid",
                        "cards": [
                            {
                                "type": "heading",
                                "heading": "Media Details Card - Example 1",
                            },
                            {
                                "type": "custom:stremio-media-details-card",
                                "entity": entity_id,
                                "show_backdrop": True,
                                "show_cast": True,
                                "show_genres": True,
                                "show_description": True,
                                "show_progress": True,
                                "expand_description": True,
                                "max_cast": 8,
                                "max_description_lines": 3,
                                "grid_options": {"columns": "full"},
                            },
                        ],
                    },
                    # Media details card - second instance
                    {
                        "type": "grid",
                        "cards": [
                            {
                                "type": "heading",
                                "heading": "Media Details Card - Example 2",
                            },
                            {
                                "type": "custom:stremio-media-details-card",
                                "entity": entity_id,
                                "show_backdrop": True,
                                "show_cast": True,
                                "show_genres": True,
                                "show_description": True,
                                "show_progress": True,
                                "expand_description": True,
                                "max_cast": 8,
                                "max_description_lines": 3,
                                "grid_options": {"columns": "full"},
                            },
                        ],
                    },
                    # Player card - compact mode ON
                    {
                        "type": "grid",
                        "cards": [
                            {
                                "type": "heading",
                                "heading": "stremio player card, compact mode ON",
                                "heading_style": "title",
                            },
                            {
                                "type": "custom:stremio-player-card",
                                "entity": entity_id,
                                "show_poster": True,
                                "show_progress": True,
                                "show_actions": True,
                                "show_browse_button": True,
                                "show_backdrop": True,
                                "compact_mode": True,
                                "grid_options": {"columns": "full"},
                            },
                        ],
                    },
                    # Player card - compact mode OFF
                    {
                        "type": "grid",
                        "cards": [
                            {
                                "type": "heading",
                                "heading": "stremio player card, compact mode OFF",
                                "heading_style": "title",
                            },
                            {
                                "type": "custom:stremio-player-card",
                                "entity": entity_id,
                                "show_poster": True,
                                "show_progress": True,
                                "show_actions": True,
                                "show_browse_button": True,
                                "show_backdrop": True,
                                "compact_mode": False,
                                "grid_options": {"columns": "full"},
                            },
                        ],
                    },
                    # Recommendations card - horizontal scroll ON
                    {
                        "type": "grid",
                        "cards": [
                            {
                                "type": "heading",
                                "heading": "Recommendations card, horizontal scroll ON",
                                "heading_style": "title",
                            },
                            {
                                "type": "custom:stremio-recommendations-card",
                                "title": "Recommended For You",
                                "show_filters": True,
                                "show_title": True,
                                "show_reason": True,
                                "show_media_type_badge": True,
                                "max_items": 20,
                                "columns": 3,
                                "card_height": 0,
                                "poster_aspect_ratio": "2/3",
                                "horizontal_scroll": True,
                                "tap_action": "details",
                                "default_filter": "all",
                                "grid_options": {"columns": "full"},
                            },
                        ],
                    },
                    # Recommendations card - horizontal scroll OFF
                    {
                        "type": "grid",
                        "cards": [
                            {
                                "type": "heading",
                                "heading": "Recommendations card, horizontal scroll OFF",
                                "heading_style": "title",
                            },
                            {
                                "type": "custom:stremio-recommendations-card",
                                "title": "Recommended For You",
                                "show_filters": True,
                                "show_title": True,
                                "show_reason": True,
                                "show_media_type_badge": True,
                                "max_items": 20,
                                "columns": 3,
                                "card_height": 0,
                                "poster_aspect_ratio": "2/3",
                                "horizontal_scroll": False,
                                "tap_action": "details",
                                "default_filter": "all",
                                "grid_options": {"columns": "full"},
                            },
                        ],
                    },
                ],
            }
        ]
    }


async def async_create_testing_dashboard(
    hass: HomeAssistant, entity_id: str
) -> None:
    """Create a Stremio testing dashboard.

    Args:
        hass: Home Assistant instance
        entity_id: The entity ID of the Stremio media player

    Raises:
        HomeAssistantError: If dashboard creation fails
    """
    try:
        from homeassistant.components import lovelace
        from homeassistant.helpers import storage

        # Access the lovelace storage directly
        dashboards_store = storage.Store(
            hass, 
            lovelace.dashboard.DASHBOARDS_STORAGE_VERSION, 
            lovelace.dashboard.DASHBOARDS_STORAGE_KEY
        )
        
        # Load existing dashboards
        dashboards_data = await dashboards_store.async_load() or {"items": []}
        
        # Check if dashboard already exists
        existing_dashboard = None
        for dashboard in dashboards_data.get("items", []):
            if dashboard.get("url_path") == DASHBOARD_URL_PATH:
                existing_dashboard = dashboard
                break
        
        # Create or update dashboard metadata
        if existing_dashboard:
            _LOGGER.info("Stremio testing dashboard already exists, will update content")
            dashboard_id = existing_dashboard["id"]
        else:
            # Generate a unique ID for the dashboard
            import uuid
            dashboard_id = str(uuid.uuid4())
            
            # Add new dashboard to storage
            new_dashboard = {
                "id": dashboard_id,
                "url_path": DASHBOARD_URL_PATH,
                "title": DASHBOARD_TITLE,
                "icon": DASHBOARD_ICON,
                "show_in_sidebar": True,
                "require_admin": False,
            }
            dashboards_data.setdefault("items", []).append(new_dashboard)
            await dashboards_store.async_save(dashboards_data)
            _LOGGER.info("Created Stremio testing dashboard metadata with ID: %s", dashboard_id)

        # Now create/update the dashboard content
        config_store = storage.Store(
            hass,
            lovelace.dashboard.CONFIG_STORAGE_VERSION,
            lovelace.dashboard.CONFIG_STORAGE_KEY.format(dashboard_id)
        )
        
        # Generate the dashboard configuration
        config = get_testing_dashboard_config(entity_id)
        
        # Save the dashboard content
        await config_store.async_save({"config": config})
        _LOGGER.info("Updated Stremio testing dashboard configuration")
        
        # Fire lovelace updated event to refresh the UI
        hass.bus.async_fire(EVENT_LOVELACE_UPDATED, {"url_path": DASHBOARD_URL_PATH})
        
        _LOGGER.info("Successfully created Stremio testing dashboard at /%s", DASHBOARD_URL_PATH)

    except Exception as err:
        _LOGGER.exception("Failed to create testing dashboard: %s", err)
        raise HomeAssistantError(f"Failed to create testing dashboard: {err}") from err
