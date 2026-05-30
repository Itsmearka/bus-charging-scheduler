"""
Scenario loader for the Bus Charging Scheduler.

This module handles loading and parsing scenario JSON files,
validating the data, and constructing the world state.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List

from src.models import (
    WorldConfig, Segment, Route, Station, Bus, Scenario,
    Direction
)
from src.exceptions import ScenarioLoadError, ValidationError, ConfigurationError
from src.logging_config import get_logger

logger = get_logger(__name__)


class ScenarioLoader:
    """
    Loads and validates scenario JSON files.
    
    This class is responsible for:
    - Reading JSON scenario files
    - Validating the structure and data
    - Constructing Python objects from JSON data
    - Providing the complete Scenario object to the scheduler
    """
    
    def __init__(self, scenarios_dir: str = "scenarios"):
        """
        Initialize the scenario loader.
        
        Args:
            scenarios_dir: Directory containing scenario JSON files
        """
        self.scenarios_dir = Path(scenarios_dir)
    
    def load_scenario(self, scenario_name: str) -> Scenario:
        """
        Load a specific scenario by name.
        
        Args:
            scenario_name: Name of the scenario file (without .json extension)
            
        Returns:
            Scenario object containing all world state
            
        Raises:
            FileNotFoundError: If scenario file doesn't exist
            ValueError: If scenario data is invalid
        """
        scenario_file = self.scenarios_dir / f"{scenario_name}.json"
        
        if not scenario_file.exists():
            raise FileNotFoundError(f"Scenario file not found: {scenario_file}")
        
        with open(scenario_file, 'r') as f:
            data = json.load(f)
        
        # Validate and parse the scenario
        return self._parse_scenario(data)
    
    def list_scenarios(self) -> List[str]:
        """
        List all available scenario files.
        
        Returns:
            List of scenario names (without .json extension)
        """
        if not self.scenarios_dir.exists():
            return []
        
        scenarios = []
        for file in self.scenarios_dir.glob("*.json"):
            scenarios.append(file.stem)
        return sorted(scenarios)
    
    def _parse_scenario(self, data: Dict) -> Scenario:
        """
        Parse JSON data into a Scenario object.
        
        Args:
            data: Raw JSON data as dictionary
            
        Returns:
            Parsed Scenario object
            
        Raises:
            ValueError: If required fields are missing or invalid
        """
        # Parse metadata
        metadata = data.get("metadata", {})
        if not metadata.get("name"):
            raise ValueError("Scenario metadata must include 'name'")
        
        # Parse world config
        world_config_data = data.get("world_config", {})
        world_config = self._parse_world_config(world_config_data)
        
        # Parse routes
        routes_data = data.get("routes", {})
        routes = {}
        for route_id, route_data in routes_data.items():
            routes[route_id] = self._parse_route(route_id, route_data)
        
        # Parse stations
        stations_data = data.get("stations", {})
        stations = {}
        for station_id, station_data in stations_data.items():
            stations[station_id] = self._parse_station(station_id, station_data)
        
        # Parse buses
        buses_data = data.get("buses", [])
        buses = []
        for bus_data in buses_data:
            buses.append(self._parse_bus(bus_data, routes))
        
        # Parse weights (merge with defaults)
        weights_data = data.get("weights", {})
        weights = world_config.default_weights.copy()
        weights.update(weights_data)
        
        return Scenario(
            metadata=metadata,
            world_config=world_config,
            routes=routes,
            stations=stations,
            buses=buses,
            weights=weights
        )
    
    def _parse_world_config(self, data: Dict) -> WorldConfig:
        """
        Parse world configuration.
        
        Args:
            data: World config JSON data
            
        Returns:
            WorldConfig object
        """
        return WorldConfig(
            battery_range_km=data.get("battery_range_km", 240.0),
            charging_time_min=data.get("charging_time_min", 25.0),
            travel_speed_kmh=data.get("travel_speed_kmh", 60.0),
            default_weights=data.get("default_weights", {
                "individual": 1.0,
                "operator": 1.0,
                "overall": 1.0
            })
        )
    
    def _parse_route(self, route_id: str, data: Dict) -> Route:
        """
        Parse a route definition.
        
        Args:
            route_id: Route identifier
            data: Route JSON data
            
        Returns:
            Route object
        """
        segments_data = data.get("segments", [])
        segments = []
        total_distance = 0.0
        
        for seg_data in segments_data:
            segment = Segment(
                from_station=seg_data["from_station"],
                to_station=seg_data["to_station"],
                distance_km=seg_data["distance_km"]
            )
            segments.append(segment)
            total_distance += segment.distance_km
        
        return Route(
            route_id=route_id,
            name=data.get("name", route_id),
            segments=segments,
            total_distance=total_distance
        )
    
    def _parse_station(self, station_id: str, data: Dict) -> Station:
        """
        Parse a station definition.
        
        Args:
            station_id: Station identifier
            data: Station JSON data
            
        Returns:
            Station object
        """
        return Station(
            station_id=station_id,
            name=data.get("name", station_id),
            num_chargers=data.get("num_chargers", 1)
        )
    
    def _parse_bus(self, data: Dict, routes: Dict[str, Route]) -> Bus:
        """
        Parse a bus definition.
        
        Args:
            data: Bus JSON data
            routes: Dictionary of routes for validation
            
        Returns:
            Bus object
            
        Raises:
            ValidationError: If route_id is invalid or bus data is invalid
        """
        route_id = data.get("route_id")
        if route_id and route_id not in routes:
            raise ValidationError(f"Bus {data.get('bus_id')} references unknown route_id: {route_id}")
        
        # Parse direction string to enum
        try:
            direction_str = data["direction"]
            direction = Direction(direction_str)
        except KeyError as e:
            raise ValidationError(f"Bus {data.get('bus_id')} missing required field: direction") from e
        except ValueError as e:
            raise ValidationError(
                f"Invalid direction '{direction_str}' for bus {data.get('bus_id')}. "
                f"Valid values: {[d.value for d in Direction]}"
            ) from e
        
        return Bus(
            bus_id=data["bus_id"],
            operator=data["operator"],
            route_id=route_id,
            direction=direction,
            departure_time=data["departure_time"]
        )
