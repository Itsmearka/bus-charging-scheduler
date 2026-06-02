"""
Utility functions for Bus Charging Scheduler.
Provides time conversion, distance calculations, and validation helpers.
"""

from typing import List, Tuple
import config
from src.models import Bus


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


def get_route_stations_in_order(direction: str) -> List[str]:
    """
    Get the list of stations in route order for a given direction.
    
    Args:
        direction: 'BK' for Bengaluru→Kochi, 'KB' for Kochi→Bengaluru
        
    Returns:
        List of station IDs in route order
        
    Example:
        >>> get_route_stations_in_order('BK')
        ['A', 'B', 'C', 'D']
        >>> get_route_stations_in_order('KB')
        ['D', 'C', 'B', 'A']
    """
    if direction == 'BK':
        return config.STATIONS  # A, B, C, D
    elif direction == 'KB':
        return config.STATIONS[::-1]  # D, C, B, A (reverse)
    else:
        raise ValueError(f"Invalid direction: {direction}")


def get_station_distance_from_origin(station_id: str, direction: str) -> int:
    """
    Get the distance of a station from the origin (Bengaluru for BK, Kochi for KB).
    
    Args:
        station_id: Station ID (e.g., 'A', 'B', 'C', 'D')
        direction: 'BK' for Bengaluru→Kochi, 'KB' for Kochi→Bengaluru
        
    Returns:
        Distance from origin in kilometers
        
    Example:
        >>> get_station_distance_from_origin('A', 'BK')
        100
        >>> get_station_distance_from_origin('D', 'KB')
        100
    """
    if direction == 'BK':
        return config.STATION_LOCATIONS_KM[station_id]
    elif direction == 'KB':
        # Distance from Kochi = total distance - distance from Bengaluru
        return config.TOTAL_ROUTE_DISTANCE_KM - config.STATION_LOCATIONS_KM[station_id]
    else:
        raise ValueError(f"Invalid direction: {direction}")


def calculate_distance_between_stations(from_station: str, to_station: str, direction: str) -> int:
    """
    Calculate distance between two stations along the route.
    
    Args:
        from_station: Starting station ID
        to_station: Ending station ID
        direction: Travel direction
        
    Returns:
        Distance in kilometers
        
    Example:
        >>> calculate_distance_between_stations('A', 'B', 'BK')
        120
        >>> calculate_distance_between_stations('D', 'C', 'KB')
        120
    """
    from_dist = get_station_distance_from_origin(from_station, direction)
    to_dist = get_station_distance_from_origin(to_station, direction)
    return abs(to_dist - from_dist)


def get_segment_distances(direction: str) -> List[Tuple[str, str, int]]:
    """
    Get route segments with distances for a given direction.
    
    Args:
        direction: 'BK' for Bengaluru→Kochi, 'KB' for Kochi→Bengaluru
        
    Returns:
        List of tuples (from_location, to_location, distance_km)
    """
    if direction == 'BK':
        return config.ROUTE_SEGMENTS
    elif direction == 'KB':
        # Reverse the segments
        return [(to_loc, from_loc, dist) for from_loc, to_loc, dist in reversed(config.ROUTE_SEGMENTS)]
    else:
        raise ValueError(f"Invalid direction: {direction}")


def validate_range_compliance(
    charging_stations: List[str],
    direction: str,
    battery_range: int
) -> bool:
    """
    Validate that a bus can travel between charging stations without exceeding battery range.
    
    Args:
        charging_stations: List of station IDs where bus charges (in route order)
        direction: Travel direction
        battery_range: Maximum distance bus can travel on full charge
        
    Returns:
        True if range constraints are satisfied, False otherwise
        
    Example:
        >>> validate_range_compliance(['A', 'C'], 'BK', 240)
        True  # Bengaluru→A (100km), A→C (200km), C→Kochi (220km) - all within range
        >>> validate_range_compliance(['A'], 'BK', 240)
        False  # A→Kochi is 440km, exceeds 240km range
    """
    stations_in_order = get_route_stations_in_order(direction)
    
    # Calculate distances from origin for each station
    distances_from_origin = {}
    for station in stations_in_order:
        distances_from_origin[station] = get_station_distance_from_origin(station, direction)
    
    # Check each segment between charges
    # Segment 1: origin to first charge
    # Segment 2: between charges
    # Segment 3: last charge to destination
    
    # Origin to first charge
    if charging_stations:
        first_station = charging_stations[0]
        distance_to_first = distances_from_origin[first_station]
        if distance_to_first > battery_range:
            return False
    
    # Between charges
    for i in range(len(charging_stations) - 1):
        from_station = charging_stations[i]
        to_station = charging_stations[i + 1]
        distance = abs(distances_from_origin[to_station] - distances_from_origin[from_station])
        if distance > battery_range:
            return False
    
    # Last charge to destination
    if charging_stations:
        last_station = charging_stations[-1]
        distance_from_last = distances_from_origin[last_station]
        distance_to_dest = config.TOTAL_ROUTE_DISTANCE_KM - distance_from_last
        if distance_to_dest > battery_range:
            return False
    
    # If no charging stations, check if entire trip is within range
    if not charging_stations:
        total_distance = config.TOTAL_ROUTE_DISTANCE_KM
        return total_distance <= battery_range
    
    return True


def generate_dynamic_buses(
    num_forward: int,
    num_reverse: int,
    start_time_forward: str,
    start_time_reverse: str,
    interval_minutes: int
) -> List[Bus]:
    """
    Generate buses dynamically based on configuration.
    
    Args:
        num_forward: Number of forward (BK) buses
        num_reverse: Number of reverse (KB) buses
        start_time_forward: Start time for forward buses (HH:MM)
        start_time_reverse: Start time for reverse buses (HH:MM)
        interval_minutes: Departure interval in minutes
    
    Returns:
        List of Bus objects
    """
    buses = []
    operators = config.OPERATORS
    
    # Convert start times to minutes
    start_forward_min = time_to_minutes(start_time_forward)
    start_reverse_min = time_to_minutes(start_time_reverse)
    
    # Generate forward buses
    for i in range(1, num_forward + 1):
        operator = operators[(i - 1) % len(operators)]
        departure_min = start_forward_min + (i - 1) * interval_minutes
        buses.append(Bus(
            id=f"bus_forward_{i}",
            operator=operator,
            direction="BK",
            departure_time_minutes=departure_min
        ))
    
    # Generate reverse buses
    for i in range(1, num_reverse + 1):
        operator = operators[(i - 1) % len(operators)]
        departure_min = start_reverse_min + (i - 1) * interval_minutes
        buses.append(Bus(
            id=f"bus_reverse_{i}",
            operator=operator,
            direction="KB",
            departure_time_minutes=departure_min
        ))
    
    return buses
