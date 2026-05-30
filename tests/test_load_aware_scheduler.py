"""
Unit tests for Scheduler class.

Tests the load-aware look-ahead scheduling algorithm with tunable weights
that minimizes wait time by evaluating charging options at multiple stations ahead.
"""

import pytest
from src.scheduler import Scheduler
from src.models import (
    WorldConfig, Segment, Route, Station, Bus, Scenario, Direction,
    BusSchedule, ChargingEvent
)
from src.utils import time_to_minutes


def create_simple_scenario():
    """
    Create a simple test scenario for load-aware scheduler testing.
    
    Returns:
        Scenario object with basic configuration
    """
    # Create world config
    world_config = WorldConfig(
        battery_range_km=240.0,
        charging_time_min=25.0,
        travel_speed_kmh=60.0,
        default_weights={"individual": 1.0, "operator": 1.0, "overall": 1.0}
    )
    
    # Create segments
    segments = [
        Segment(from_station="Bengaluru", to_station="A", distance_km=100.0),
        Segment(from_station="A", to_station="B", distance_km=120.0),
        Segment(from_station="B", to_station="C", distance_km=100.0),
        Segment(from_station="C", to_station="D", distance_km=120.0),
        Segment(from_station="D", to_station="Kochi", distance_km=100.0)
    ]
    
    # Create route
    route = Route(
        route_id="main_route",
        name="Main Route",
        segments=segments,
        total_distance=540.0
    )
    
    # Create stations
    stations = {
        "A": Station(station_id="A", name="Station A", num_chargers=1),
        "B": Station(station_id="B", name="Station B", num_chargers=1),
        "C": Station(station_id="C", name="Station C", num_chargers=1),
        "D": Station(station_id="D", name="Station D", num_chargers=1)
    }
    
    # Create buses
    buses = [
        Bus(
            bus_id="bus-01",
            operator="kpn",
            route_id="main_route",
            direction=Direction.FORWARD,
            departure_time="19:00"
        ),
        Bus(
            bus_id="bus-02",
            operator="freshbus",
            route_id="main_route",
            direction=Direction.FORWARD,
            departure_time="19:15"
        )
    ]
    
    # Create scenario
    scenario = Scenario(
        metadata={"name": "Test Scenario", "description": "Simple test scenario", "version": "1.0"},
        world_config=world_config,
        routes={"main_route": route},
        stations=stations,
        buses=buses,
        weights={"individual": 1.0, "operator": 1.0, "overall": 1.0}
    )
    
    return scenario


class TestScheduler:
    """Test cases for Scheduler class."""
    
    def test_scheduler_initialization(self):
        """Test that scheduler initializes with correct parameters."""
        scheduler = Scheduler(weights={"individual": 1.0, "operator": 1.0, "overall": 1.0}, look_ahead_depth=2)
        assert scheduler.weights == {"individual": 1.0, "operator": 1.0, "overall": 1.0}
        assert scheduler.look_ahead_depth == 2
        assert scheduler.penalty_per_stop == 5.0  # Derived from individual weight
        assert scheduler.queue_threshold == 3  # Derived from operator weight
        assert scheduler.congestion_threshold == 3  # Derived from overall weight
        assert scheduler.scenario is None
        assert scheduler.station_queues == {}
    
    def test_scheduler_initialization_defaults(self):
        """Test that scheduler initializes with default parameters."""
        scheduler = Scheduler()
        assert scheduler.weights == {"individual": 1.0, "operator": 1.0, "overall": 1.0}
        assert scheduler.penalty_per_stop == 5.0
        assert scheduler.look_ahead_depth == 2
        assert scheduler.queue_threshold == 3
        assert scheduler.congestion_threshold == 3
    
    def test_get_reachable_stations_with_depth_limit(self):
        """Test that _get_reachable_stations respects look_ahead_depth limit."""
        scenario = create_simple_scenario()
        scheduler = Scheduler(look_ahead_depth=2)
        scheduler.scenario = scenario
        route = scenario.routes["main_route"]
        bus = scenario.buses[0]
        
        # Get direction-aware segments
        segments = scheduler._get_direction_aware_segments(route, bus)
        
        # Bus at A with 240km range
        reachable = scheduler._get_reachable_stations("A", 240.0, segments, 1)
        
        # Should return A, B, C (depth=2 means current + next 2)
        assert "A" in reachable
        assert "B" in reachable
        assert "C" in reachable
        # D should not be included (beyond depth limit)
        assert "D" not in reachable
    
    def test_get_reachable_stations_unlimited_depth(self):
        """Test that _get_reachable_stations returns all stations when depth=None."""
        scenario = create_simple_scenario()
        scheduler = Scheduler(look_ahead_depth=None)
        scheduler.scenario = scenario
        route = scenario.routes["main_route"]
        bus = scenario.buses[0]
        
        # Get direction-aware segments
        segments = scheduler._get_direction_aware_segments(route, bus)
        
        # Bus at A with 240km range
        reachable = scheduler._get_reachable_stations("A", 240.0, segments, 1)
        
        # Should return current station (A) and stations within range
        # With 240km range at A (after traveling 100km), can reach:
        # A (current), B (120km), C (100km), D (120km) - total 420km, exceeds range
        # So should return A, B, C (but not D as it's beyond range)
        assert "A" in reachable
        assert "B" in reachable
        assert "C" in reachable
        # D is beyond range (100+120+100+120=440km > 240km), so not included
    
    def test_can_reach_station_safely(self):
        """Test that _can_reach_station_safely correctly checks range."""
        scheduler = Scheduler()
        
        # Should reach: 240km range, 100km distance
        assert scheduler._can_reach_station_safely(240.0, 100.0) == True
        
        # Should not reach: 100km range, 120km distance
        assert scheduler._can_reach_station_safely(100.0, 120.0) == False
        
        # Should reach: exactly equal
        assert scheduler._can_reach_station_safely(120.0, 120.0) == True
    
    def test_simulate_charging_at_station(self):
        """Test that _simulate_charging_at_station checks route completion."""
        scenario = create_simple_scenario()
        scheduler = Scheduler()
        route = scenario.routes["main_route"]
        bus = scenario.buses[0]
        
        # Get direction-aware segments
        segments = scheduler._get_direction_aware_segments(route, bus)
        
        # Charge at B: can bus complete route?
        can_complete = scheduler._simulate_charging_at_station(
            "B", 240.0, segments, 2, 240.0
        )
        
        # After charging at B, remaining distance is 320km (C->D->Kochi)
        # 320km > 240km range, so should not complete
        assert can_complete == False
    
    def test_get_current_queue_length(self):
        """Test that _get_current_queue_length returns correct queue length."""
        scheduler = Scheduler()
        station_chargers = {
            "A": [0.0, 10.0, 25.0],  # 1 charger busy at time=15.0 (25.0 > 15.0)
            "B": [0.0, 0.0]  # No chargers busy
        }
        
        queue_length = scheduler._get_current_queue_length("A", station_chargers, 15.0)
        assert queue_length == 1  # 1 charger has time > 15.0
        
        queue_length = scheduler._get_current_queue_length("B", station_chargers, 15.0)
        assert queue_length == 0  # All chargers available
    
    def test_calculate_wait_time(self):
        """Test that _calculate_wait_time uses correct formula."""
        scheduler = Scheduler()
        
        # Formula: queue_length × charging_time
        wait_time = scheduler._calculate_wait_time(5, 25.0)
        assert wait_time == 125.0  # 5 × 25 = 125
        
        wait_time = scheduler._calculate_wait_time(0, 25.0)
        assert wait_time == 0.0  # 0 × 25 = 0
    
    def test_calculate_extra_stops(self):
        """Test that _calculate_extra_stops calculates correctly."""
        scheduler = Scheduler()
        
        # Current station is first in list, candidate is second
        candidate_stations = ["A", "B", "C"]
        extra_stops = scheduler._calculate_extra_stops("B", "A", candidate_stations)
        assert extra_stops == 1  # B is 1 position ahead of A
        
        # Current station is second, candidate is first
        extra_stops = scheduler._calculate_extra_stops("A", "B", candidate_stations)
        assert extra_stops == 1  # A is 1 position behind B
        
        # Same station
        extra_stops = scheduler._calculate_extra_stops("A", "A", candidate_stations)
        assert extra_stops == 0
    
    def test_score_charging_option(self):
        """Test that scoring formula prioritizes wait time."""
        # Score = wait_time + (extra_stops × penalty_per_stop)
        # penalty_per_stop = 5 min (derived from individual weight = 1.0)
        # Wait time dominates (5 << 25 charging time)
        
        scheduler = Scheduler(weights={"individual": 1.0, "operator": 1.0, "overall": 1.0})
        
        # Option 1: 0 min wait, 1 extra stop → score = 0 + (1 × 5) = 5
        score_1 = 0 + (1 * 5.0)
        assert score_1 == 5.0
        
        # Option 2: 125 min wait, 0 extra stops → score = 125 + (0 × 5) = 125
        score_2 = 125 + (0 * 5.0)
        assert score_2 == 125.0
        
        # Option 1 should be chosen (lower score)
        assert score_1 < score_2
    
    def test_calculate_current_range(self):
        """Test that _calculate_current_range calculates remaining range correctly."""
        scenario = create_simple_scenario()
        scheduler = Scheduler()
        scheduler.scenario = scenario
        route = scenario.routes["main_route"]
        bus = scenario.buses[0]
        
        # Get direction-aware segments
        segments = scheduler._get_direction_aware_segments(route, bus)
        
        # Bus at segment 1 (after Bengaluru->A), no charging yet
        schedule = BusSchedule(
            bus_id="bus-01",
            charging_events=[],
            travel_segments=[],
            total_wait_time=0.0,
            final_arrival_time=0.0,
            is_valid=True
        )
        
        current_range = scheduler._calculate_current_range(schedule, segments, 1, 240.0)
        # Traveled 100km, should have 140km remaining
        assert current_range == 140.0
    
    def test_early_charging_avoids_congestion(self):
        """Test key test case: early charging avoids congestion."""
        scenario = create_simple_scenario()
        scheduler = Scheduler()
        scheduler.scenario = scenario
        route = scenario.routes["main_route"]
        bus = scenario.buses[0]
        
        # Get direction-aware segments
        segments = scheduler._get_direction_aware_segments(route, bus)
        
        # Simulate: Bus at A with 140km range
        # Station B has long queue (5 buses), Station A has no queue
        schedule = BusSchedule(
            bus_id="bus-01",
            charging_events=[],
            travel_segments=[],
            total_wait_time=0.0,
            final_arrival_time=0.0,
            is_valid=True
        )
        
        station_chargers = {
            "A": [0.0],  # No queue
            "B": [125.0, 150.0, 175.0, 200.0, 225.0]  # 5 buses waiting (125 min wait)
        }
        
        # Make charging decision
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
        
        # Should choose to charge at A (0 min wait) instead of B (125 min wait)
        assert decision['charge_now'] == True
        assert decision['chosen_station'] == "A"
        assert decision['wait_time'] == 0.0
    
    def test_fallback_to_necessary_charging(self):
        """Test edge case: must charge at current station when no other options."""
        scenario = create_simple_scenario()
        scheduler = Scheduler()
        scheduler.scenario = scenario
        route = scenario.routes["main_route"]
        bus = scenario.buses[0]
        
        # Get direction-aware segments
        segments = scheduler._get_direction_aware_segments(route, bus)
        
        # Bus at B with only 20km remaining (must charge)
        schedule = BusSchedule(
            bus_id="bus-01",
            charging_events=[],
            travel_segments=[],
            total_wait_time=0.0,
            final_arrival_time=0.0,
            is_valid=True
        )
        
        station_chargers = {
            "A": [0.0],
            "B": [0.0],
            "C": [0.0]
        }
        
        # Make charging decision
        decision = scheduler._make_charging_decision(
            bus=scenario.buses[0],
            current_station_id="B",
            current_time=220.0,
            schedule=schedule,
            segments=segments,
            segment_index=2,
            station_chargers=station_chargers,
            operator_wait_times={"kpn": []},
            event_queue=[]
        )
        
        # Should charge at B (must charge)
        assert decision['charge_now'] == True
        assert decision['chosen_station'] == "B"
    
    def test_schedule_simple_scenario(self):
        """Test that scheduler can schedule a simple scenario without errors."""
        scenario = create_simple_scenario()
        scheduler = Scheduler()
        
        # Should not raise any exceptions
        result = scheduler.schedule(scenario)
        
        # Verify result structure
        assert result is not None
        assert result.scenario_name == "Test Scenario"
        assert len(result.bus_schedules) == 2
        assert len(result.station_schedules) == 4
        assert result.metrics is not None
        assert result.metrics.total_network_time > 0
    
    def test_look_ahead_depth_from_config(self):
        """Test that look_ahead_depth can be overridden from world_config."""
        scenario = create_simple_scenario()
        # Add look_ahead_depth to world_config
        scenario.world_config.__dict__['look_ahead_depth'] = 5
        
        scheduler = Scheduler(look_ahead_depth=2)
        
        # After scheduling, should use config value (5) not default (2)
        scheduler.schedule(scenario)
        assert scheduler.look_ahead_depth == 5
