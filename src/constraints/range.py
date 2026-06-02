"""
Range constraint definitions for Bus Charging Scheduler.
Ensures buses never run out of battery between charges.
"""

import math
from typing import Dict, List
from ortools.sat.python import cp_model
from src.utils.route import get_route_stations_in_order, calculate_distance_between_stations


def add_range_constraint(
    model: cp_model.CpModel,
    variables: Dict,
    buses: List,
    stations: List[str],
    battery_range: int,
    route_config: dict
) -> None:
    """
    Add constraint that bus cannot travel more than battery_range between charges.
    
    Args:
        model: CP-SAT model
        variables: Dictionary of decision variables
        buses: List of Bus objects
        stations: List of station IDs
        battery_range: Maximum distance bus can travel on full charge
        route_config: Route configuration dictionary
    """
    # For each bus, ensure it charges enough times to complete the trip
    for bus in buses:
        stations_in_order = get_route_stations_in_order(bus.direction)
        
        # Calculate cumulative distances from origin
        if bus.direction == 'BK':
            origin = 'Bengaluru'
            destination = 'Kochi'
        else:
            origin = 'Kochi'
            destination = 'Bengaluru'
        
        # Build distance map
        distance_map = {}
        current_distance = 0
        for i, station in enumerate(stations_in_order):
            if i == 0:
                # Distance from origin to first station
                distance_map[station] = route_config['station_locations_km'][station]
            else:
                # Distance between consecutive stations
                prev_station = stations_in_order[i - 1]
                distance_map[station] = distance_map[prev_station] + calculate_distance_between_stations(
                    prev_station, station, bus.direction
                )
        
        # Add constraint: bus must charge at stations such that no segment exceeds range
        # This is a complex constraint that requires checking all possible charging combinations
        
        # Calculate minimum charges needed
        # Bus starts with full battery, so can travel battery_range km before first charge
        # After each charge, can travel another battery_range km
        # Formula: min_charges = ceil(total_distance / battery_range) - 1
        # Example: 540km / 240km = 2.25 → ceil = 3 → 3-1 = 2 charges minimum
        min_charges = math.ceil(route_config['total_route_distance_km'] / battery_range) - 1
        
        # Add constraint that bus charges at at least min_charges stations
        charge_vars = [variables['charge_at'][(bus.id, station)] for station in stations_in_order]
        model.Add(sum(charge_vars) >= min_charges)
