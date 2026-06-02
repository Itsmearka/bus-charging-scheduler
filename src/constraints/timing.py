"""
Timing constraint definitions for Bus Charging Scheduler.
Constraints for charging duration, travel time, and arrival-start relationships.
"""

from typing import Dict, List
from ortools.sat.python import cp_model
from src.utils.route import get_route_stations_in_order, calculate_distance_between_stations, get_station_distance_from_origin
from src.utils.time import calculate_travel_time


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
