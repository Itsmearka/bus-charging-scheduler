"""
Capacity constraint definitions for Bus Charging Scheduler.
Ensures only one bus can use a charger at a time.
"""

from typing import Dict, List
from ortools.sat.python import cp_model
import config
from src.utils.route import get_route_stations_in_order, get_station_distance_from_origin


def _filter_buses_by_reachability(buses: List, station: str) -> List:
    """
    Phase 2 optimization: Filter out buses that cannot possibly reach this station.
    
    Args:
        buses: List of Bus objects
        station: Station ID
    
    Returns:
        Filtered list of buses that can reach the station
    """
    filtered = []
    for bus in buses:
        stations_in_order = get_route_stations_in_order(bus.direction)
        if station in stations_in_order:
            filtered.append(bus)
    return filtered


def add_charger_capacity_constraint(
    model: cp_model.CpModel,
    variables: Dict,
    buses: List,
    stations: List[str],
    chargers_per_station: Dict[str, int],
    enable_optimizations: bool
) -> None:
    """
    Add constraint that only one bus can use a charger at a time.
    
    Args:
        model: CP-SAT model
        variables: Dictionary of decision variables
        buses: List of Bus objects
        stations: List of station IDs
        chargers_per_station: Number of chargers at each station
        enable_optimizations: Whether to use Phase 2 optimizations
    """
    # For each station, ensure no two buses charge at the same time
    for station in stations:
        # Get all buses that might charge at this station
        buses_at_station = [bus for bus in buses if (bus.id, station) in variables['charge_at']]
        
        # Phase 2 optimization: Filter buses by earliest possible arrival time
        if enable_optimizations and len(buses_at_station) > 20:
            buses_at_station = _filter_buses_by_reachability(buses_at_station, station)
        
        # For each pair of buses, ensure their charging windows don't overlap
        for i in range(len(buses_at_station)):
            for j in range(i + 1, len(buses_at_station)):
                bus_i = buses_at_station[i]
                bus_j = buses_at_station[j]
                
                # Phase 2 optimization: Skip ordering constraint if buses can't possibly conflict
                # Calculate earliest possible arrival times based on departure
                if enable_optimizations:
                    distance_to_station_i = get_station_distance_from_origin(station, bus_i.direction)
                    distance_to_station_j = get_station_distance_from_origin(station, bus_j.direction)
                    
                    earliest_arrival_i = bus_i.departure_time_minutes + int((distance_to_station_i / config.BUS_SPEED_KMH) * 60)
                    earliest_arrival_j = bus_j.departure_time_minutes + int((distance_to_station_j / config.BUS_SPEED_KMH) * 60)
                    
                    # If buses arrive more than TIME_WINDOW_THRESHOLD apart, skip constraint
                    time_diff = abs(earliest_arrival_i - earliest_arrival_j)
                    if time_diff > config.TIME_WINDOW_THRESHOLD_MINUTES + config.CHARGING_TIME_MINUTES:
                        continue
                
                # Add no-overlap constraint using ordering variable
                order_var = variables['order'][(bus_i.id, bus_j.id, station)]
                
                # If order_var = 1, bus_i charges before bus_j
                # If order_var = 0, bus_j charges before bus_i
                
                # Constraint: end_time_i <= start_time_j OR end_time_j <= start_time_i
                start_i = variables['start_time'][(bus_i.id, station)]
                end_i = variables['end_time'][(bus_i.id, station)]
                start_j = variables['start_time'][(bus_j.id, station)]
                end_j = variables['end_time'][(bus_j.id, station)]
                
                # If bus_i charges at station and bus_j charges at station
                charge_i = variables['charge_at'][(bus_i.id, station)]
                charge_j = variables['charge_at'][(bus_j.id, station)]
                
                # Create boolean literal for both charging
                both_charge = model.NewBoolVar(f"both_charge_{bus_i.id}_{bus_j.id}_{station}")
                model.AddBoolAnd([charge_i, charge_j]).OnlyEnforceIf(both_charge)
                model.AddBoolOr([charge_i.Not(), charge_j.Not()]).OnlyEnforceIf(both_charge.Not())
                
                # If both charge, enforce ordering
                model.Add(end_i <= start_j).OnlyEnforceIf([both_charge, order_var])
                model.Add(end_j <= start_i).OnlyEnforceIf([both_charge, order_var.Not()])


def add_symmetry_breaking_constraint(
    model: cp_model.CpModel,
    variables: Dict,
    buses: List,
    stations: List[str],
    enable_optimizations: bool = False
) -> None:
    """
    Add symmetry-breaking constraints to eliminate duplicate solutions.
    
    For buses with same operator and direction, enforce lexicographic ordering
    on charging decisions to avoid symmetric solutions.
    
    Args:
        model: CP-SAT model
        variables: Dictionary of decision variables
        buses: List of Bus objects
        stations: List of station IDs
        enable_optimizations: Whether to use Phase 2 optimizations
    """
    if not enable_optimizations:
        return
    
    # Conservative approach: only break symmetry for buses with identical departure times
    # Group buses by operator and direction
    bus_groups = {}
    for bus in buses:
        key = (bus.operator, bus.direction, bus.departure_time_minutes)
        if key not in bus_groups:
            bus_groups[key] = []
        bus_groups[key].append(bus)
    
    # For each group with identical departure times, add symmetry-breaking
    for (operator, direction, departure), group_buses in bus_groups.items():
        if len(group_buses) > 1:
            # Sort by bus ID to establish ordering
            group_buses.sort(key=lambda b: b.id)
            for i in range(len(group_buses) - 1):
                bus_i = group_buses[i]
                bus_j = group_buses[i + 1]
                for station in stations:
                    charge_i = variables['charge_at'][(bus_i.id, station)]
                    charge_j = variables['charge_at'][(bus_j.id, station)]
                    model.Add(charge_i >= charge_j)
