"""
Data models for the Bus Charging Scheduler.

This module defines the core data structures used throughout the application.
All models use type hints for clarity and validation.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum


class Direction(str, Enum):
    """
    Travel direction for buses.
    
    Represents the direction of travel along a route.
    """
    FORWARD = "forward"
    REVERSE = "reverse"


@dataclass
class WorldConfig:
    """
    Global configuration for the world/simulation.
    
    Attributes:
        battery_range_km: Maximum distance a bus can travel on full charge (default: 240 km)
        charging_time_min: Time required to charge battery to full (default: 25 minutes)
        travel_speed_kmh: Constant travel speed for all buses (default: 60 km/h)
        default_weights: Default weights for optimization rules
    """
    battery_range_km: float = 240.0
    charging_time_min: float = 25.0
    travel_speed_kmh: float = 60.0
    
    # Default weights for soft rules (can be overridden per scenario)
    default_weights: Dict[str, float] = field(default_factory=lambda: {
        "individual": 1.0,
        "operator": 1.0,
        "overall": 1.0
    })


@dataclass
class Segment:
    """
    A route segment connecting two stations.
    
    Attributes:
        from_station: ID of the starting station
        to_station: ID of the ending station
        distance_km: Distance in kilometers
    """
    from_station: str
    to_station: str
    distance_km: float


@dataclass
class Route:
    """
    A route defined by an ordered sequence of segments.
    
    Attributes:
        route_id: Unique identifier for the route
        name: Human-readable name
        segments: Ordered list of segments from origin to destination
        total_distance: Total distance of the route in km
    """
    route_id: str
    name: str
    segments: List[Segment]
    total_distance: float
    
    def get_station_sequence(self) -> List[str]:
        """
        Get the ordered list of station IDs along the route.
        
        Returns:
            List of station IDs from origin to destination
        """
        if not self.segments:
            return []
        
        stations = [self.segments[0].from_station]
        for segment in self.segments:
            stations.append(segment.to_station)
        return stations
    
    def get_segment_distance(self, from_station: str, to_station: str) -> float:
        """
        Get distance between two consecutive stations on the route.
        
        Args:
            from_station: Starting station ID
            to_station: Ending station ID
            
        Returns:
            Distance in km, or 0 if stations not found or not consecutive
        """
        for segment in self.segments:
            if segment.from_station == from_station and segment.to_station == to_station:
                return segment.distance_km
        return 0.0


@dataclass
class Station:
    """
    A charging station along the route.
    
    Attributes:
        station_id: Unique identifier (e.g., "A", "B", "C", "D")
        name: Human-readable name
        num_chargers: Number of chargers at this station (default: 1)
    """
    station_id: str
    name: str
    num_chargers: int = 1


@dataclass
class Bus:
    """
    A bus that needs to be scheduled.
    
    Attributes:
        bus_id: Unique identifier (e.g., "bus-BK-01")
        operator: Operating company (e.g., "kpn", "freshbus", "flixbus")
        route_id: ID of the route this bus travels
        direction: Travel direction (forward or reverse)
        departure_time: Departure time from origin (as time string "HH:MM")
    """
    bus_id: str
    operator: str
    route_id: str
    direction: Direction
    departure_time: str  # "HH:MM" format


@dataclass
class ChargingEvent:
    """
    A single charging event for a bus.
    
    Attributes:
        station_id: ID of the charging station
        arrival_time: When bus arrived at station (minutes from start of day)
        charge_start_time: When charging actually started (may be after waiting)
        charge_end_time: When charging completed
        wait_time: How long bus waited for charger (minutes)
    """
    station_id: str
    arrival_time: float
    charge_start_time: float
    charge_end_time: float
    wait_time: float


@dataclass
class TravelSegment:
    """
    A travel segment in a bus's journey.
    
    Attributes:
        from_station: Starting station ID
        to_station: Ending station ID
        departure_time: Departure time in minutes
        arrival_time: Arrival time in minutes
        distance_km: Distance traveled
    """
    from_station: str
    to_station: str
    departure_time: float
    arrival_time: float
    distance_km: float


@dataclass
class BusSchedule:
    """
    Complete schedule for a single bus.
    
    Attributes:
        bus_id: Unique identifier of the bus
        charging_events: List of all charging events
        travel_segments: List of all travel segments
        total_wait_time: Total waiting time across all stations
        final_arrival_time: Arrival time at destination (minutes from start)
        is_valid: Whether the schedule is valid (no range violations)
    """
    bus_id: str
    charging_events: List[ChargingEvent]
    travel_segments: List[TravelSegment]
    total_wait_time: float
    final_arrival_time: float
    is_valid: bool = True


@dataclass
class StationSchedule:
    """
    Schedule for a single charging station.
    
    Attributes:
        station_id: Unique identifier of the station
        charging_queue: Ordered list of charging events at this station
        utilization_metrics: Optional utilization statistics
    """
    station_id: str
    charging_queue: List[Dict[str, float]]  # Each dict: {"bus_id": str, "start": float, "end": float}
    utilization_metrics: Optional[Dict[str, float]] = None


@dataclass
class ScheduleMetrics:
    """
    Aggregate metrics for the entire schedule.
    
    Attributes:
        total_network_time: Sum of all bus completion times
        avg_wait_per_bus: Average wait time across all buses
        avg_wait_per_operator: Average wait time per operator
        max_wait_time: Maximum wait time for any single bus
    """
    total_network_time: float
    avg_wait_per_bus: float
    avg_wait_per_operator: Dict[str, float]
    max_wait_time: float


@dataclass
class ScheduleResult:
    """
    Complete result of scheduling a scenario.
    
    Attributes:
        scenario_name: Name of the scenario that was scheduled
        timestamp: When the schedule was generated
        weights_used: Weights that were applied
        bus_schedules: Per-bus schedules
        station_schedules: Per-station schedules
        metrics: Aggregate metrics
    """
    scenario_name: str
    timestamp: str
    weights_used: Dict[str, float]
    bus_schedules: List[BusSchedule]
    station_schedules: List[StationSchedule]
    metrics: ScheduleMetrics


@dataclass
class Scenario:
    """
    Complete scenario definition.
    
    Attributes:
        metadata: Scenario metadata (name, description, version)
        world_config: Global configuration
        routes: All routes in the world
        stations: All stations in the world
        buses: All buses to be scheduled
        weights: Optimization weights (overrides defaults)
    """
    metadata: Dict[str, str]
    world_config: WorldConfig
    routes: Dict[str, Route]
    stations: Dict[str, Station]
    buses: List[Bus]
    weights: Dict[str, float]
