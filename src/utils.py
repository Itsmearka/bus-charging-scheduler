"""
Utility functions for the Bus Charging Scheduler.

This module provides helper functions for time conversion, distance calculations,
and other common operations.
"""

import logging
from typing import List, Tuple

from src.exceptions import RangeConstraintViolation, ValidationError
from src.logging_config import get_logger

logger = get_logger(__name__)


def time_to_minutes(time_str: str) -> float:
    """
    Convert time string "HH:MM" to minutes from midnight.
    
    Args:
        time_str: Time in format "HH:MM" (24-hour)
        
    Returns:
        Minutes from midnight as float
        
    Example:
        "19:00" -> 1140.0
        "19:15" -> 1155.0
    """
    hours, minutes = map(int, time_str.split(':'))
    return hours * 60.0 + minutes


def minutes_to_time(minutes: float) -> str:
    """
    Convert minutes from midnight to time string "HH:MM".
    
    Args:
        minutes: Minutes from midnight as float
        
    Returns:
        Time string in format "HH:MM"
        
    Example:
        1140.0 -> "19:00"
        1155.0 -> "19:15"
    """
    hours = int(minutes // 60)
    mins = int(minutes % 60)
    return f"{hours:02d}:{mins:02d}"


def calculate_travel_time(distance_km: float, speed_kmh: float) -> float:
    """
    Calculate travel time in minutes given distance and speed.
    
    Args:
        distance_km: Distance in kilometers
        speed_kmh: Speed in kilometers per hour
        
    Returns:
        Travel time in minutes
        
    Raises:
        ValidationError: If speed is zero or negative
        
    Example:
        distance_km=100, speed_kmh=60 -> 100.0 minutes
    """
    if speed_kmh <= 0:
        raise ValidationError(f"Speed must be positive, got {speed_kmh}")
    return (distance_km / speed_kmh) * 60.0


def calculate_distance_travelled(time_minutes: float, speed_kmh: float) -> float:
    """
    Calculate distance travelled given time and speed.
    
    Args:
        time_minutes: Time in minutes
        speed_kmh: Speed in kilometers per hour
        
    Returns:
        Distance in kilometers
    """
    return (time_minutes / 60.0) * speed_kmh


def format_duration(minutes: float) -> str:
    """
    Format duration in minutes to human-readable string.
    
    Args:
        minutes: Duration in minutes
        
    Returns:
        Formatted string (e.g., "1h 30m" or "45m")
    """
    hours = int(minutes // 60)
    mins = int(minutes % 60)
    
    if hours > 0 and mins > 0:
        return f"{hours}h {mins}m"
    elif hours > 0:
        return f"{hours}h"
    else:
        return f"{mins}m"


def validate_range_constraint(
    distance_km: float,
    battery_range_km: float,
    bus_id: str,
    from_station: str,
    to_station: str
) -> Tuple[bool, str]:
    """
    Validate that a segment distance doesn't exceed battery range.
    
    Args:
        distance_km: Distance to travel
        battery_range_km: Maximum battery range
        bus_id: Bus identifier for error message
        from_station: Starting station
        to_station: Ending station
        
    Returns:
        Tuple of (is_valid, error_message)
        
    Raises:
        RangeConstraintViolation: If distance exceeds battery range
    """
    if distance_km > battery_range_km:
        error_msg = (
            f"Bus {bus_id} cannot travel from {from_station} to {to_station} "
            f"({distance_km} km) without charging (battery range: {battery_range_km} km)"
        )
        logger.error(error_msg)
        raise RangeConstraintViolation(error_msg)
    return True, ""


def get_route_segments_for_direction(
    route_segments: List,
    direction: str
) -> List:
    """
    Get route segments in the correct order based on direction.
    
    Args:
        route_segments: List of segments in forward direction
        direction: "forward" or "reverse"
        
    Returns:
        List of segments in the correct order
        
    Raises:
        ValidationError: If direction is invalid
    """
    from src.models import Direction
    
    try:
        direction_enum = Direction(direction)
    except ValueError as e:
        raise ValidationError(
            f"Invalid direction '{direction}'. "
            f"Valid values: {[d.value for d in Direction]}"
        ) from e
    
    if direction_enum == Direction.FORWARD:
        return route_segments
    elif direction_enum == Direction.REVERSE:
        # Reverse the segments and swap from/to stations
        reversed_segments = []
        for segment in reversed(route_segments):
            reversed_segments.append({
                "from_station": segment["to_station"],
                "to_station": segment["from_station"],
                "distance_km": segment["distance_km"]
            })
        return reversed_segments
