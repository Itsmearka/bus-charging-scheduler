"""
Route utility functions for Bus Charging Scheduler.
Provides distance calculations and route validation helpers.
"""

from typing import List, Tuple
import config


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
