"""
Time utility functions for Bus Charging Scheduler.
Provides time conversion and travel time calculations.
"""


def time_to_minutes(time_str: str) -> int:
    """
    Convert time string in HH:MM format to minutes from midnight.
    
    Args:
        time_str: Time string in format "HH:MM" (24-hour format)
        
    Returns:
        Minutes from midnight
        
    Example:
        >>> time_to_minutes("19:00")
        1140
        >>> time_to_minutes("00:30")
        30
    """
    hours, minutes = map(int, time_str.split(':'))
    return hours * 60 + minutes


def minutes_to_time(minutes: int) -> str:
    """
    Convert minutes from midnight to time string in HH:MM format.
    
    Args:
        minutes: Minutes from midnight
        
    Returns:
        Time string in format "HH:MM" (24-hour format)
        
    Example:
        >>> minutes_to_time(1140)
        '19:00'
        >>> minutes_to_time(30)
        '00:30'
    """
    hours = (minutes // 60) % 24
    mins = minutes % 60
    return f"{hours:02d}:{mins:02d}"


def calculate_travel_time(distance_km: int, speed_kmh: int) -> int:
    """
    Calculate travel time in minutes given distance and speed.
    
    Args:
        distance_km: Distance to travel in kilometers
        speed_kmh: Speed in kilometers per hour
        
    Returns:
        Travel time in minutes
        
    Example:
        >>> calculate_travel_time(100, 60)
        100
        >>> calculate_travel_time(120, 60)
        120
    """
    # time = distance / speed, convert hours to minutes
    return int((distance_km / speed_kmh) * 60)
