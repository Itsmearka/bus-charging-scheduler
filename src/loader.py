"""
Scenario loader for Bus Charging Scheduler.
Loads JSON scenario files, validates them, and merges with global config.
"""

import json
from pathlib import Path
from typing import List, Optional
import config
from src.models import Scenario, Bus
from src.utils import time_to_minutes


def load_scenario(scenario_path: str) -> Scenario:
    """
    Load a scenario from a JSON file and validate it.
    
    Args:
        scenario_path: Path to the scenario JSON file
        
    Returns:
        Validated Scenario object
        
    Raises:
        FileNotFoundError: If scenario file doesn't exist
        ValueError: If scenario data is invalid
    """
    path = Path(scenario_path)
    if not path.exists():
        raise FileNotFoundError(f"Scenario file not found: {scenario_path}")
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    # Convert bus departure times from strings to minutes
    buses_data = data.get('buses', [])
    buses = []
    for bus_data in buses_data:
        # Convert departure_time string to minutes
        departure_str = bus_data['departure_time']
        departure_minutes = time_to_minutes(departure_str)
        
        # Create Bus object with converted time
        bus = Bus(
            id=bus_data['id'],
            operator=bus_data['operator'],
            direction=bus_data['direction'],
            departure_time_minutes=departure_minutes,
            # Future extension fields (not used yet)
            priority=bus_data.get('priority'),
            route_id=bus_data.get('route_id')
        )
        buses.append(bus)
    
    # Create Scenario object
    scenario = Scenario(
        name=data['name'],
        description=data.get('description', ''),
        buses=buses,
        weights=data['weights'],
        # Optional config overrides
        battery_range_km=data.get('battery_range_km'),
        charging_time_minutes=data.get('charging_time_minutes'),
        bus_speed_kmh=data.get('bus_speed_kmh')
    )
    
    return scenario


def get_scenario_config(scenario: Scenario) -> dict:
    """
    Get the effective configuration for a scenario, merging with global config.
    
    Args:
        scenario: Scenario object
        
    Returns:
        Dictionary with effective configuration values
    """
    effective_config = {
        'battery_range_km': scenario.battery_range_km if scenario.battery_range_km else config.BATTERY_RANGE_KM,
        'charging_time_minutes': scenario.charging_time_minutes if scenario.charging_time_minutes else config.CHARGING_TIME_MINUTES,
        'bus_speed_kmh': scenario.bus_speed_kmh if scenario.bus_speed_kmh else config.BUS_SPEED_KMH,
        'weights': scenario.weights,
        'route_segments': config.ROUTE_SEGMENTS,
        'stations': config.STATIONS,
        'chargers_per_station': config.CHARGERS_PER_STATION,
        'total_route_distance_km': config.TOTAL_ROUTE_DISTANCE_KM,
        'station_locations_km': config.STATION_LOCATIONS_KM,
        'enable_optimizations': config.ENABLE_CONSTRAINT_OPTIMIZATIONS,
        'time_window_threshold_minutes': config.TIME_WINDOW_THRESHOLD_MINUTES,
        'solver_time_limit_seconds': config.SOLVER_TIME_LIMIT_SECONDS,
        'linearization_level': config.LINEARIZATION_LEVEL,
        'enable_hints': config.ENABLE_HINTS,
        'cp_model_presolve': config.CP_MODEL_PRESOLVE,
        'max_number_of_conflicts': config.MAX_NUMBER_OF_CONFLICTS,
    }
    
    return effective_config


def list_available_scenarios(scenarios_dir: str = "data/scenarios") -> List[str]:
    """
    List all available scenario files in the scenarios directory.
    
    Args:
        scenarios_dir: Directory containing scenario JSON files
        
    Returns:
        List of scenario file paths
    """
    path = Path(scenarios_dir)
    if not path.exists():
        return []
    
    # Find all JSON files in the scenarios directory
    scenario_files = sorted(path.glob("*.json"))
    return [str(f) for f in scenario_files]


def load_scenario_by_name(scenario_name: str, scenarios_dir: str = "data/scenarios") -> Optional[Scenario]:
    """
    Load a scenario by its name (filename without .json extension).
    
    Args:
        scenario_name: Name of the scenario (e.g., "scenario_1_even_spacing")
        scenarios_dir: Directory containing scenario JSON files
        
    Returns:
        Scenario object if found, None otherwise
    """
    scenario_path = Path(scenarios_dir) / f"{scenario_name}.json"
    if scenario_path.exists():
        return load_scenario(str(scenario_path))
    return None


def get_scenario_display_name(scenario_path: str) -> str:
    """
    Get a display-friendly name from a scenario file path.
    
    Args:
        scenario_path: Path to scenario file
        
    Returns:
        Display-friendly name (extracted from filename or scenario data)
    """
    try:
        scenario = load_scenario(scenario_path)
        return scenario.name
    except Exception:
        # If loading fails, return filename without extension
        return Path(scenario_path).stem
