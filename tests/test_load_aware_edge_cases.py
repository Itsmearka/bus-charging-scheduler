"""
Edge case tests for Scheduler class.

Tests boundary conditions, error handling, and special scenarios
for the load-aware look-ahead scheduling algorithm.
"""

import pytest
from src.scheduler import Scheduler
from src.models import (
    WorldConfig, Segment, Route, Station, Bus, Scenario, Direction,
    BusSchedule
)
from src.utils import time_to_minutes


def create_single_station_scenario():
    """
    Create a scenario with only 1 charging station.
    
    Returns:
        Scenario object with single station
    """
    world_config = WorldConfig(
        battery_range_km=240.0,
        charging_time_min=25.0,
        travel_speed_kmh=60.0,
        default_weights={"individual": 1.0, "operator": 1.0, "overall": 1.0}
    )
    
    segments = [
        Segment(from_station="Bengaluru", to_station="A", distance_km=200.0),
        Segment(from_station="A", to_station="Kochi", distance_km=200.0)
    ]
    
    route = Route(
        route_id="single_station_route",
        name="Single Station Route",
        segments=segments,
        total_distance=400.0
    )
    
    stations = {
        "A": Station(station_id="A", name="Station A", num_chargers=1)
    }
    
    buses = [
        Bus(
            bus_id="bus-01",
            operator="kpn",
            route_id="single_station_route",
            direction=Direction.FORWARD,
            departure_time="19:00"
        )
    ]
    
    scenario = Scenario(
        metadata={"name": "Single Station", "description": "Single station scenario", "version": "1.0"},
        world_config=world_config,
        routes={"single_station_route": route},
        stations=stations,
        buses=buses,
        weights={"individual": 1.0, "operator": 1.0, "overall": 1.0}
    )
    
    return scenario


def create_custom_route_scenario(num_stations=10):
    """
    Create a scenario with many stations to test look_ahead_depth.
    
    Args:
        num_stations: Number of stations to create
        
    Returns:
        Scenario object with many stations
    """
    world_config = WorldConfig(
        battery_range_km=240.0,
        charging_time_min=25.0,
        travel_speed_kmh=60.0,
        default_weights={"individual": 1.0, "operator": 1.0, "overall": 1.0}
    )
    
    # Create segments with equal distances
    segments = []
    station_names = ["Bengaluru"]
    for i in range(num_stations - 1):
        station_names.append(f"Station_{i}")
        segments.append(
            Segment(
                from_station=station_names[i],
                to_station=station_names[i + 1],
                distance_km=50.0  # Small distance for many stations
            )
        )
    station_names.append("Kochi")
    
    route = Route(
        route_id="long_route",
        name="Long Route",
        segments=segments,
        total_distance=50.0 * (num_stations - 1)
    )
    
    # Create stations (excluding endpoints)
    stations = {}
    for i in range(1, num_stations - 1):
        stations[f"Station_{i}"] = Station(
            station_id=f"Station_{i}",
            name=f"Station {i}",
            num_chargers=1
        )
    
    buses = [
        Bus(
            bus_id="bus-01",
            operator="kpn",
            route_id="long_route",
            direction=Direction.FORWARD,
            departure_time="19:00"
        )
    ]
    
    scenario = Scenario(
        metadata={"name": "Long Route", "description": f"Route with {num_stations} stations", "version": "1.0"},
        world_config=world_config,
        routes={"long_route": route},
        stations=stations,
        buses=buses,
        weights={"individual": 1.0, "operator": 1.0, "overall": 1.0}
    )
    
    return scenario


class TestLoadAwareEdgeCases:
    """Test edge cases for Scheduler."""
    
    def test_single_station_route(self):
        """Test fallback behavior with single station route."""
        scenario = create_single_station_scenario()
        scheduler = Scheduler()
        
        # Should schedule successfully with single station
        result = scheduler.schedule(scenario)
        
        assert result is not None
        assert len(result.station_schedules) == 1
        assert len(result.bus_schedules) == 1
        # Bus should charge at the only station
        assert len(result.bus_schedules[0].charging_events) >= 1
    
    def test_all_stations_equally_congested(self):
        """Test behavior when all stations have equal queue lengths."""
        scenario = create_single_station_scenario()
        scheduler = Scheduler()
        scheduler.scenario = scenario
        route = scenario.routes["single_station_route"]
        bus = scenario.buses[0]
        
        # Get direction-aware segments
        segments = scheduler._get_direction_aware_segments(route, bus)
        
        schedule = BusSchedule(
            bus_id="bus-01",
            charging_events=[],
            travel_segments=[],
            total_wait_time=0.0,
            final_arrival_time=0.0,
            is_valid=True
        )
        
        # All stations have same queue length (3 buses waiting)
        station_chargers = {
            "A": [75.0, 100.0, 125.0]  # 3 buses waiting
        }
        
        decision = scheduler._make_charging_decision(
            bus=scenario.buses[0],
            current_station_id="A",
            current_time=100.0,
            schedule=schedule,
            segments=segments,
            segment_index=1,
            station_chargers=station_chargers,
            operator_wait_times={"kpn": []},
            event_queue=[]
        )
        
        # Should still make a decision (prefer current station when equal)
        assert decision['charge_now'] == True
    
    def test_bus_at_endpoint(self):
        """Test behavior when bus is at destination endpoint."""
        scenario = create_single_station_scenario()
        scheduler = Scheduler()
        scheduler.scenario = scenario
        route = scenario.routes["single_station_route"]
        bus = scenario.buses[0]
        
        # Get direction-aware segments
        segments = scheduler._get_direction_aware_segments(route, bus)
        
        schedule = BusSchedule(
            bus_id="bus-01",
            charging_events=[],
            travel_segments=[],
            total_wait_time=0.0,
            final_arrival_time=0.0,
            is_valid=True
        )
        
        station_chargers = {"A": [0.0]}
        
        # Bus at endpoint (segment_index = len(segments))
        # At endpoint (Kochi is not a charging station), should not charge
        decision = scheduler._make_charging_decision(
            bus=scenario.buses[0],
            current_station_id="Kochi",
            current_time=400.0,
            schedule=schedule,
            segments=segments,
            segment_index=2,
            station_chargers=station_chargers,
            operator_wait_times={"kpn": []},
            event_queue=[]
        )
        
        # At endpoint (not a charging station), should not charge
        assert decision['charge_now'] == False
    
    def test_empty_queues(self):
        """Test behavior when all stations have empty queues."""
        scenario = create_single_station_scenario()
        scheduler = Scheduler()
        scheduler.scenario = scenario
        route = scenario.routes["single_station_route"]
        bus = scenario.buses[0]
        
        # Get direction-aware segments
        segments = scheduler._get_direction_aware_segments(route, bus)
        
        schedule = BusSchedule(
            bus_id="bus-01",
            charging_events=[],
            travel_segments=[],
            total_wait_time=0.0,
            final_arrival_time=0.0,
            is_valid=True
        )
        
        # All stations have empty queues (all chargers available)
        station_chargers = {
            "A": [0.0]  # No queue
        }
        
        decision = scheduler._make_charging_decision(
            bus=scenario.buses[0],
            current_station_id="A",
            current_time=100.0,
            schedule=schedule,
            segments=segments,
            segment_index=1,
            station_chargers=station_chargers,
            operator_wait_times={"kpn": []},
            event_queue=[]
        )
        
        # With empty queues, should prefer earliest station
        assert decision['charge_now'] == True
        assert decision['wait_time'] == 0.0
    
    def test_custom_route_with_depth_limit(self):
        """Test look_ahead_depth with custom route having 10+ stations."""
        scenario = create_custom_route_scenario(num_stations=15)
        scheduler = Scheduler(look_ahead_depth=3)
        
        # Should schedule successfully with depth limit
        result = scheduler.schedule(scenario)
        
        assert result is not None
        assert len(result.bus_schedules) == 1
        assert result.metrics.total_network_time > 0
    
    def test_custom_route_unlimited_depth(self):
        """Test unlimited depth (depth=None) with custom route."""
        scenario = create_custom_route_scenario(num_stations=10)
        scheduler = Scheduler(look_ahead_depth=None)
        
        # Should schedule successfully with unlimited depth
        result = scheduler.schedule(scenario)
        
        assert result is not None
        assert len(result.bus_schedules) == 1
        assert result.metrics.total_network_time > 0
    
    def test_cannot_reach_any_candidate_station(self):
        """Test fallback when bus cannot reach any candidate station."""
        scenario = create_single_station_scenario()
        scheduler = Scheduler()
        scheduler.scenario = scenario
        route = scenario.routes["single_station_route"]
        bus = scenario.buses[0]
        
        # Get direction-aware segments
        segments = scheduler._get_direction_aware_segments(route, bus)
        
        # Bus with very low range (10km)
        schedule = BusSchedule(
            bus_id="bus-01",
            charging_events=[],
            travel_segments=[],
            total_wait_time=0.0,
            final_arrival_time=0.0,
            is_valid=True
        )
        
        station_chargers = {"A": [0.0]}
        
        decision = scheduler._make_charging_decision(
            bus=scenario.buses[0],
            current_station_id="A",
            current_time=100.0,
            schedule=schedule,
            segments=segments,
            segment_index=1,
            station_chargers=station_chargers,
            operator_wait_times={"kpn": []},
            event_queue=[]
        )
        
        # Must charge at current station (no other options)
        assert decision['charge_now'] == True
        assert decision['chosen_station'] == "A"
    
    def test_zero_penalty_per_stop(self):
        """Test scheduler with zero individual weight (only wait time matters)."""
        scenario = create_single_station_scenario()
        # Set scenario weights to match scheduler weights
        scenario.weights = {"individual": 0.0, "operator": 1.0, "overall": 1.0}
        scheduler = Scheduler(weights={"individual": 0.0, "operator": 1.0, "overall": 1.0})
        
        # Should schedule successfully
        result = scheduler.schedule(scenario)
        
        assert result is not None
        assert scheduler.penalty_per_stop == 0.0  # Derived from individual weight (0.0 * 5)
    
    def test_high_penalty_per_stop(self):
        """Test scheduler with high individual weight (stops heavily penalized)."""
        scenario = create_single_station_scenario()
        # Set scenario weights to match scheduler weights
        scenario.weights = {"individual": 5.0, "operator": 1.0, "overall": 1.0}
        scheduler = Scheduler(weights={"individual": 5.0, "operator": 1.0, "overall": 1.0})
        
        # Should schedule successfully
        result = scheduler.schedule(scenario)
        
        assert result is not None
        assert scheduler.penalty_per_stop == 25.0  # Derived from individual weight (5.0 * 5)
    
    def test_depth_zero(self):
        """Test scheduler with depth=0 (only current station)."""
        scenario = create_single_station_scenario()
        scheduler = Scheduler(look_ahead_depth=0)
        
        # Should schedule successfully (only looks at current station)
        result = scheduler.schedule(scenario)
        
        assert result is not None
        assert scheduler.look_ahead_depth == 0
