"""Shared entity helpers for Stremio integration.

This module contains helper functions and base classes for Stremio entities
to ensure consistency and reduce code duplication.
"""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo

from .const import DOMAIN


def get_device_info(entry: ConfigEntry) -> DeviceInfo:
    """Generate device info for Stremio entities.

    Args:
        entry: The config entry for this integration.

    Returns:
        DeviceInfo dictionary for entity registration.
    """
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=f"Stremio {entry.data.get('email', 'Account')}",
        manufacturer="Stremio",
        model="Stremio Integration",
        entry_type=DeviceEntryType.SERVICE,
    )


def format_time(seconds: int | float | None) -> str:
    """Format seconds into human-readable time string.

    Args:
        seconds: Number of seconds to format.

    Returns:
        Formatted string like "1:30:00" or "45:30".
    """
    if not seconds or seconds <= 0:
        return "0:00"

    seconds = int(seconds)
    hours = seconds // 3600
    mins = (seconds % 3600) // 60
    secs = seconds % 60

    if hours > 0:
        return f"{hours}:{mins:02d}:{secs:02d}"
    return f"{mins}:{secs:02d}"


def calculate_progress_percent(position: int | float, duration: int | float) -> float:
    """Calculate progress percentage.

    Args:
        position: Current position in seconds.
        duration: Total duration in seconds.

    Returns:
        Progress as percentage (0-100), rounded to 1 decimal place.
    """
    if not duration or duration <= 0:
        return 0.0
    return round((position / duration) * 100, 1)
