"""
Constraint definitions for Bus Charging Scheduler.
Contains hard and soft constraints for the CP-SAT solver.
"""

from typing import Dict, List, Tuple
from ortools.sat.python import cp_model
import config
from src.utils import get_route_stations_in_order, calculate_distance_between_stations, get_station_distance_from_origin


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
        import math
        min_charges = math.ceil(route_config['total_route_distance_km'] / battery_range) - 1
        
        # Add constraint that bus charges at at least min_charges stations
        charge_vars = [variables['charge_at'][(bus.id, station)] for station in stations_in_order]
        model.Add(sum(charge_vars) >= min_charges)


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


def add_charging_duration_constraint(
    model: cp_model.CpModel,
    variables: Dict,
    buses: List,
    stations: List[str],
    charging_time: int
) -> None:
    """
    Add constraint that charging always takes exactly charging_time minutes.
    
    Args:
        model: CP-SAT model
        variables: Dictionary of decision variables
        buses: List of Bus objects
        stations: List of station IDs
        charging_time: Time required for charging in minutes
    """
    # For each bus and station, if charging, end_time = start_time + charging_time
    for bus in buses:
        for station in stations:
            charge_var = variables['charge_at'][(bus.id, station)]
            start_time = variables['start_time'][(bus.id, station)]
            end_time = variables['end_time'][(bus.id, station)]
            
            # If charging, enforce duration
            model.Add(end_time == start_time + charging_time).OnlyEnforceIf(charge_var)
            
            # If not charging, set start and end to 0 (or a sentinel value)
            model.Add(start_time == 0).OnlyEnforceIf(charge_var.Not())
            model.Add(end_time == 0).OnlyEnforceIf(charge_var.Not())


def add_travel_time_constraint(
    model: cp_model.CpModel,
    variables: Dict,
    buses: List,
    stations: List[str],
    speed_kmh: int,
    route_config: dict
) -> None:
    """
    Add constraint that travel time between stations is correct.
    
    Args:
        model: CP-SAT model
        variables: Dictionary of decision variables
        buses: List of Bus objects
        stations: List of station IDs
        speed_kmh: Bus speed in km/h
        route_config: Route configuration dictionary
    """
    # For each bus, calculate arrival times at stations based on departure and travel
    for bus in buses:
        stations_in_order = get_route_stations_in_order(bus.direction)
        
        # Calculate travel time from departure to first station
        if stations_in_order:
            first_station = stations_in_order[0]
            distance_to_first = get_station_distance_from_origin(first_station, bus.direction)
            travel_time = int((distance_to_first / speed_kmh) * 60)
            
            # Arrival at first station = departure + travel time
            arrival_first = variables['arrival_time'][(bus.id, first_station)]
            model.Add(arrival_first == bus.departure_time_minutes + travel_time)
            
            # Calculate arrival times for subsequent stations
            for i in range(1, len(stations_in_order)):
                prev_station = stations_in_order[i - 1]
                current_station = stations_in_order[i]
                
                distance = calculate_distance_between_stations(prev_station, current_station, bus.direction)
                travel_time = int((distance / speed_kmh) * 60)
                
                # Arrival depends on whether bus charged at previous station
                charge_prev = variables['charge_at'][(bus.id, prev_station)]
                end_prev = variables['end_time'][(bus.id, prev_station)]
                arrival_prev = variables['arrival_time'][(bus.id, prev_station)]
                
                # If charged at previous station, arrival = end_prev + travel
                # If not charged, arrival = arrival_prev + travel
                arrival_current = variables['arrival_time'][(bus.id, current_station)]
                
                # Enforce exact arrival time based on charging decision
                model.Add(arrival_current == end_prev + travel_time).OnlyEnforceIf(charge_prev)
                model.Add(arrival_current == arrival_prev + travel_time).OnlyEnforceIf(charge_prev.Not())


def add_arrival_start_constraint(
    model: cp_model.CpModel,
    variables: Dict,
    buses: List,
    stations: List[str]
) -> None:
    """
    Add constraint that charging start time >= arrival time.
    
    Args:
        model: CP-SAT model
        variables: Dictionary of decision variables
        buses: List of Bus objects
        stations: List of station IDs
    """
    # For each bus and station, start_time >= arrival_time
    for bus in buses:
        for station in stations:
            arrival_time = variables['arrival_time'][(bus.id, station)]
            start_time = variables['start_time'][(bus.id, station)]
            charge_var = variables['charge_at'][(bus.id, station)]
            
            # If charging, start_time >= arrival_time
            model.Add(start_time >= arrival_time).OnlyEnforceIf(charge_var)


def calculate_individual_penalty(
    variables: Dict,
    buses: List,
    stations: List[str]
) -> cp_model.IntVar:
    """
    Calculate penalty for individual bus wait times.
    
    Args:
        variables: Dictionary of decision variables
        buses: List of Bus objects
        stations: List of station IDs
        
    Returns:
        CP-SAT variable representing total individual penalty
    """
    # Sum of all wait times across all buses
    wait_times = []
    for bus in buses:
        for station in stations:
            wait_time = variables['wait_time'][(bus.id, station)]
            wait_times.append(wait_time)
    
    # This would need to be implemented as a linear expression in the model
    # Return None for now - this will be handled in the objective function
    return None


def calculate_operator_penalty(
    variables: Dict,
    buses: List,
    stations: List[str]
) -> Dict[str, cp_model.IntVar]:
    """
    Calculate penalty for each operator's fleet delays.
    
    Args:
        variables: Dictionary of decision variables
        buses: List of Bus objects
        stations: List of station IDs
        
    Returns:
        Dictionary mapping operator ID to penalty variable
    """
    # Group buses by operator
    operators = {}
    for bus in buses:
        if bus.operator not in operators:
            operators[bus.operator] = []
        operators[bus.operator].append(bus)
    
    # Calculate total wait time per operator
    operator_penalties = {}
    for operator, operator_buses in operators.items():
        wait_times = []
        for bus in operator_buses:
            for station in stations:
                wait_time = variables['wait_time'][(bus.id, station)]
                wait_times.append(wait_time)
        
        # This would need to be implemented as a linear expression in the model
        # Return None for now - this will be handled in the objective function
        operator_penalties[operator] = None
    
    return operator_penalties
