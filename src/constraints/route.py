"""
Route constraint definitions for Bus Charging Scheduler.
Ensures buses visit stations in route order (no backtracking).
"""

from typing import Dict, List
from ortools.sat.python import cp_model
from src.utils.route import get_route_stations_in_order


def add_route_order_constraint(
    model: cp_model.CpModel,
    variables: Dict,
    buses: List,
    stations: List[str]
) -> None:
    """
    Add constraint that buses visit stations in route order (no backtracking).
    
    Args:
        model: CP-SAT model
        variables: Dictionary of decision variables
        buses: List of Bus objects
        stations: List of station IDs
    """
    # For each bus, if it charges at station_i and station_j, they must be in route order
    for bus in buses:
        stations_in_order = get_route_stations_in_order(bus.direction)
        
        for i in range(len(stations_in_order)):
            for j in range(i + 1, len(stations_in_order)):
                station_i = stations_in_order[i]
                station_j = stations_in_order[j]
                
                charge_i = variables['charge_at'][(bus.id, station_i)]
                charge_j = variables['charge_at'][(bus.id, station_j)]
                
                # If bus charges at both stations, arrival time at j must be after arrival time at i
                arrival_i = variables['arrival_time'][(bus.id, station_i)]
                arrival_j = variables['arrival_time'][(bus.id, station_j)]
                
                # If both charging, enforce order
                model.Add(arrival_j >= arrival_i).OnlyEnforceIf([charge_i, charge_j])
