"""
Helper functions for script-based testing and output formatting.

This module provides utility functions for formatting scheduler results
in both text table and JSON formats, saving outputs to files, and
printing results to the terminal.
"""

import json
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from src.scenario_loader import ScenarioLoader
from src.scheduler import Scheduler
from src.models import Scenario


def format_output_text(result) -> str:
    """
    Format scheduler result as text tables for terminal display.
    
    Args:
        result: ScheduleResult object from scheduler
        
    Returns:
        Formatted text string with metrics, per-bus schedules, and per-station queues
    """
    output = []
    
    # Metrics section
    output.append("=== METRICS ===")
    metrics_data = [
        ["Total Network Time", f"{result.metrics.total_network_time:.1f} min"],
        ["Average Wait per Bus", f"{result.metrics.avg_wait_per_bus:.1f} min"],
        ["Max Wait Time", f"{result.metrics.max_wait_time:.1f} min"]
    ]
    metrics_df = pd.DataFrame(metrics_data, columns=["Metric", "Value"])
    output.append(metrics_df.to_string(index=False))
    
    # Weights used section
    output.append("\n=== OPTIMIZATION WEIGHTS USED ===")
    weights_data = [
        [rule, weight] for rule, weight in result.weights_used.items()
    ]
    weights_df = pd.DataFrame(weights_data, columns=["Rule", "Weight"])
    output.append(weights_df.to_string(index=False))
    
    # Per-bus schedules section
    output.append("\n=== PER-BUS SCHEDULES ===")
    bus_schedule_data = []
    for i, bus_schedule in enumerate(result.bus_schedules):
        charging_stops = len(bus_schedule.charging_events)
        total_wait = bus_schedule.total_wait_time
        bus_schedule_data.append({
            "Order": i + 1,
            "Bus ID": bus_schedule.bus_id,
            "Charging Stops": charging_stops,
            "Total Wait Time": f"{total_wait:.1f} min"
        })
    if bus_schedule_data:
        bus_df = pd.DataFrame(bus_schedule_data)
        output.append(bus_df.to_string(index=False))
    else:
        output.append("No bus schedules available.")
    
    # Per-station charging queues section
    output.append("\n=== PER-STATION CHARGING QUEUES ===")
    station_queue_data = []
    for station_schedule in result.station_schedules:
        queue_length = len(station_schedule.charging_queue)
        if queue_length > 0:
            max_wait = max(event['wait_time'] for event in station_schedule.charging_queue)
            bus_ids = [event['bus_id'] for event in station_schedule.charging_queue]
        else:
            max_wait = 0
            bus_ids = []
        station_queue_data.append({
            "Station": station_schedule.station_id,
            "Queue Length": queue_length,
            "Max Wait": f"{max_wait:.1f} min" if queue_length > 0 else "0 min",
            "Buses": ", ".join(bus_ids) if bus_ids else "None"
        })
    if station_queue_data:
        station_df = pd.DataFrame(station_queue_data)
        output.append(station_df.to_string(index=False))
    else:
        output.append("No station queues available.")
    
    return "\n".join(output)


def format_output_json(result, scenario_name: str, scenario: Optional[Scenario] = None) -> Dict[str, Any]:
    """
    Format scheduler result as structured JSON.
    
    Args:
        result: ScheduleResult object from scheduler
        scenario_name: Name of the scenario
        scenario: Optional Scenario object for additional metadata
        
    Returns:
        Dictionary with structured result data
    """
    # Build bus schedules data
    bus_schedules_data = []
    for bus_schedule in result.bus_schedules:
        charging_events_data = []
        for event in bus_schedule.charging_events:
            charging_events_data.append({
                "station_id": event.station_id,
                "arrival_time": event.arrival_time,
                "charge_start_time": event.charge_start_time,
                "charge_end_time": event.charge_end_time,
                "wait_time": event.wait_time
            })
        
        travel_segments_data = []
        for segment in bus_schedule.travel_segments:
            travel_segments_data.append({
                "from_station": segment.from_station,
                "to_station": segment.to_station,
                "departure_time": segment.departure_time,
                "arrival_time": segment.arrival_time,
                "distance_km": segment.distance_km
            })
        
        bus_schedules_data.append({
            "bus_id": bus_schedule.bus_id,
            "total_wait_time": bus_schedule.total_wait_time,
            "final_arrival_time": bus_schedule.final_arrival_time,
            "is_valid": bus_schedule.is_valid,
            "charging_events": charging_events_data,
            "travel_segments": travel_segments_data
        })
    
    # Build station schedules data
    station_schedules_data = []
    for station_schedule in result.station_schedules:
        station_schedules_data.append({
            "station_id": station_schedule.station_id,
            "charging_queue": station_schedule.charging_queue
        })
    
    # Build structured output
    output = {
        "metadata": {
            "scenario": scenario_name,
            "timestamp": datetime.now().isoformat(),
            "weights": result.weights_used
        },
        "metrics": {
            "total_network_time": result.metrics.total_network_time,
            "avg_wait_per_bus": result.metrics.avg_wait_per_bus,
            "max_wait_time": result.metrics.max_wait_time
        },
        "bus_schedules": bus_schedules_data,
        "station_schedules": station_schedules_data
    }
    
    # Add scenario metadata if available
    if scenario:
        output["scenario_metadata"] = {
            "name": scenario.metadata.get("name", ""),
            "description": scenario.metadata.get("description", ""),
            "version": scenario.metadata.get("version", ""),
            "world_config": {
                "battery_range_km": scenario.world_config.battery_range_km,
                "charging_time_min": scenario.world_config.charging_time_min,
                "travel_speed_kmh": scenario.world_config.travel_speed_kmh
            },
            "total_buses": len(scenario.buses),
            "total_stations": len(scenario.stations)
        }
    
    return output


def save_output(result, format_type: str, filename: str, scenario_name: str, scenario: Optional[Scenario] = None):
    """
    Save scheduler result to file in specified format.
    
    Args:
        result: ScheduleResult object from scheduler
        format_type: Output format ('text', 'json', or 'both')
        filename: Base filename (without extension)
        scenario_name: Name of the scenario
        scenario: Optional Scenario object for additional metadata
    """
    output_dir = Path("tests/output")
    output_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    if format_type in ["text", "both"]:
        text_filename = output_dir / f"{filename}_{timestamp}.txt"
        text_content = format_output_text(result)
        text_filename.write_text(text_content, encoding='utf-8')
        print(f"Saved text output to: {text_filename}")
    
    if format_type in ["json", "both"]:
        json_filename = output_dir / f"{filename}_{timestamp}.json"
        json_content = format_output_json(result, scenario_name, scenario)
        json_filename.write_text(json.dumps(json_content, indent=2), encoding='utf-8')
        print(f"Saved JSON output to: {json_filename}")


def print_output(result, format_type: str = "text"):
    """
    Print scheduler result to terminal in specified format.
    
    Args:
        result: ScheduleResult object from scheduler
        format_type: Output format ('text' or 'json')
    """
    if format_type == "text":
        print(format_output_text(result))
    elif format_type == "json":
        print(json.dumps(format_output_json(result, "unknown"), indent=2))
    else:
        print(f"Unsupported format: {format_type}")


def run_scenario_with_params(
    scenario_name: str,
    scenarios_dir: str = "data/scenarios",
    weights: Optional[Dict[str, float]] = None,
    battery_range_km: Optional[float] = None,
    charging_time_min: Optional[float] = None,
    travel_speed_kmh: Optional[float] = None,
    chargers_per_station: Optional[int] = None
) -> tuple[Scenario, Any]:
    """
    Load and run a scenario with custom parameters.
    
    Args:
        scenario_name: Name of the scenario file (without .json extension)
        scenarios_dir: Directory containing scenario files
        weights: Optional custom weights dictionary
        battery_range_km: Optional custom battery range
        charging_time_min: Optional custom charging time
        travel_speed_kmh: Optional custom travel speed
        chargers_per_station: Optional custom chargers per station
        
    Returns:
        Tuple of (Scenario object, ScheduleResult object)
    """
    # Load scenario
    loader = ScenarioLoader(scenarios_dir)
    scenario = loader.load_scenario(scenario_name)
    
    # Apply custom parameters if provided
    if weights:
        scenario.weights = weights
    
    if battery_range_km is not None:
        scenario.world_config.battery_range_km = battery_range_km
    
    if charging_time_min is not None:
        scenario.world_config.charging_time_min = charging_time_min
    
    if travel_speed_kmh is not None:
        scenario.world_config.travel_speed_kmh = travel_speed_kmh
    
    if chargers_per_station is not None:
        for station in scenario.stations.values():
            station.num_chargers = chargers_per_station
    
    # Run scheduler
    scheduler = Scheduler()
    result = scheduler.schedule(scenario)
    
    return scenario, result


def create_custom_scenario(
    station_names: List[str],
    distances: List[float],
    battery_range_km: float = 240.0,
    charging_time_min: float = 25.0,
    travel_speed_kmh: float = 60.0,
    chargers_per_station: int = 1,
    num_buses_per_direction: int = 10,
    departure_interval_min: int = 15,
    weights: Optional[Dict[str, float]] = None
) -> Scenario:
    """
    Create a custom scenario from parameters (for testing).
    
    This is a simplified version of the create_custom_scenario function from app.py
    for use in test scripts without UI dependencies.
    
    Args:
        station_names: List of station names in order
        distances: List of distances between consecutive stations
        battery_range_km: Maximum battery range
        charging_time_min: Charging time in minutes
        travel_speed_kmh: Travel speed in km/h
        chargers_per_station: Number of chargers per station
        num_buses_per_direction: Number of buses in each direction
        departure_interval_min: Departure interval in minutes
        weights: Optimization weights
        
    Returns:
        Custom Scenario object
    """
    from src.models import (
        WorldConfig, Route, Segment, Station, Bus, Direction, Scenario
    )
    from src.utils import minutes_to_time
    
    # Set default weights if not provided
    if weights is None:
        weights = {"individual": 1.0, "operator": 1.0, "overall": 1.0}
    
    # Create world config
    world_config = WorldConfig(
        battery_range_km=battery_range_km,
        charging_time_min=charging_time_min,
        travel_speed_kmh=travel_speed_kmh,
        default_weights=weights
    )
    
    # Create segments
    segments = []
    for i in range(len(station_names) - 1):
        segment = Segment(
            from_station=station_names[i],
            to_station=station_names[i + 1],
            distance_km=distances[i]
        )
        segments.append(segment)
    
    # Calculate total distance
    total_distance = sum(distances)
    
    # Create route
    route = Route(
        route_id="custom_route",
        name="Custom Route",
        segments=segments,
        total_distance=total_distance
    )
    
    # Create stations (exclude first and last as they are start/end cities, not charging stations)
    stations = {}
    for i, station_name in enumerate(station_names):
        # Skip first and last stations - they are start/end cities, not charging stations
        if i == 0 or i == len(station_names) - 1:
            continue
        station = Station(
            station_id=station_name,
            name=station_name,
            num_chargers=chargers_per_station
        )
        stations[station_name] = station
    
    # Create buses
    buses = []
    operators = ["kpn", "freshbus", "flixbus"]
    
    # Forward direction buses
    for i in range(num_buses_per_direction):
        departure_time = i * departure_interval_min
        departure_time_str = minutes_to_time(departure_time)
        bus = Bus(
            bus_id=f"bus-F-{i+1:02d}",
            operator=operators[i % len(operators)],
            route_id="custom_route",
            direction=Direction.FORWARD,
            departure_time=departure_time_str
        )
        buses.append(bus)
    
    # Reverse direction buses
    for i in range(num_buses_per_direction):
        departure_time = i * departure_interval_min
        departure_time_str = minutes_to_time(departure_time)
        bus = Bus(
            bus_id=f"bus-R-{i+1:02d}",
            operator=operators[i % len(operators)],
            route_id="custom_route",
            direction=Direction.REVERSE,
            departure_time=departure_time_str
        )
        buses.append(bus)
    
    # Create scenario
    scenario = Scenario(
        metadata={
            "name": "Custom Route",
            "description": f"Custom route with {len(station_names)} stations",
            "version": "1.0"
        },
        world_config=world_config,
        routes={"custom_route": route},
        stations=stations,
        buses=buses,
        weights=weights
    )
    
    return scenario
