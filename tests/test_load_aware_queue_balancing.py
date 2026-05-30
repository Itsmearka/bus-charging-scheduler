"""
Unit tests for Load-Aware Scheduler queue balancing functionality.

Tests the dynamic penalty adjustment, queue threshold logic, and load distribution
across stations to ensure the scheduler properly balances charging load.
"""

import pytest
from src.scheduler import Scheduler
from src.models import (
    WorldConfig, Segment, Route, Station, Bus, Scenario, Direction,
    BusSchedule, ChargingEvent
)
from src.utils import time_to_minutes


def create_2_station_scenario(num_buses=20):
    """
    Create a 2-station scenario for testing queue balancing.
    
    Args:
        num_buses: Number of buses to create
        
    Returns:
        Scenario object with 2 stations (A, B)
    """
    world_config = WorldConfig(
        battery_range_km=240.0,
        charging_time_min=25.0,
        travel_speed_kmh=60.0,
        default_weights={"individual": 1.0, "operator": 1.0, "overall": 1.0}
    )
    
    segments = [
        Segment(from_station="Bengaluru", to_station="A", distance_km=100.0),
        Segment(from_station="A", to_station="B", distance_km=100.0),
        Segment(from_station="B", to_station="Kochi", distance_km=100.0)
    ]
    
    route = Route(
        route_id="main_route",
        name="Main Route",
        segments=segments,
        total_distance=300.0
    )
    
    stations = {
        "A": Station(station_id="A", name="Station A", num_chargers=1),
        "B": Station(station_id="B", name="Station B", num_chargers=1)
    }
    
    buses = []
    for i in range(num_buses):
        buses.append(Bus(
            bus_id=f"bus-{i+1:02d}",
            operator="operator1",
            route_id="main_route",
            direction=Direction.FORWARD,
            departure_time=f"{19 + i//10}:{(i % 10) * 15:02d}"
        ))
    
    scenario = Scenario(
        metadata={"name": "2-Station Test", "version": "1.0"},
        world_config=world_config,
        routes={"main_route": route},
        stations=stations,
        buses=buses,
        weights={"individual": 1.0, "operator": 1.0, "overall": 1.0}
    )
    
    return scenario


def create_3_station_scenario(num_buses=20):
    """Create a 3-station scenario for testing."""
    world_config = WorldConfig(
        battery_range_km=240.0,
        charging_time_min=25.0,
        travel_speed_kmh=60.0,
        default_weights={"individual": 1.0, "operator": 1.0, "overall": 1.0}
    )
    
    segments = [
        Segment(from_station="Bengaluru", to_station="A", distance_km=80.0),
        Segment(from_station="A", to_station="B", distance_km=80.0),
        Segment(from_station="B", to_station="C", distance_km=80.0),
        Segment(from_station="C", to_station="Kochi", distance_km=80.0)
    ]
    
    route = Route(
        route_id="main_route",
        name="Main Route",
        segments=segments,
        total_distance=320.0
    )
    
    stations = {
        "A": Station(station_id="A", name="Station A", num_chargers=1),
        "B": Station(station_id="B", name="Station B", num_chargers=1),
        "C": Station(station_id="C", name="Station C", num_chargers=1)
    }
    
    buses = []
    for i in range(num_buses):
        buses.append(Bus(
            bus_id=f"bus-{i+1:02d}",
            operator="operator1",
            route_id="main_route",
            direction=Direction.FORWARD,
            departure_time=f"{19 + i//10}:{(i % 10) * 15:02d}"
        ))
    
    scenario = Scenario(
        metadata={"name": "3-Station Test", "version": "1.0"},
        world_config=world_config,
        routes={"main_route": route},
        stations=stations,
        buses=buses,
        weights={"individual": 1.0, "operator": 1.0, "overall": 1.0}
    )
    
    return scenario


class TestQueueBalancing:
    """Test cases for queue balancing functionality."""
    
    def test_dynamic_penalty_queue_threshold(self):
        """Test that queue difference threshold ignores extra_stops penalty."""
        scenario = create_2_station_scenario()
        scheduler = Scheduler(
            weights={"individual": 1.0, "operator": 1.0, "overall": 1.0}
        )
        scheduler.scenario = scenario
        
        # Test with queue difference > threshold (5 vs 0)
        penalty = scheduler._calculate_dynamic_penalty(
            current_station_queue=5,
            candidate_station_queue=0,
            num_charging_stations=2
        )
        assert penalty == 0.0  # Should ignore penalty when queue_diff > threshold
        
        # Test with queue difference <= threshold (2 vs 0)
        # Note: For 2-station routes, effective threshold is reduced to 1 (50% of 3)
        # So queue_diff=2 > effective_threshold=1, penalty=0.0
        penalty = scheduler._calculate_dynamic_penalty(
            current_station_queue=2,
            candidate_station_queue=0,
            num_charging_stations=2
        )
        assert penalty == 0.0  # Should ignore penalty due to few-station route logic
        
        # Test with many stations (normal threshold)
        penalty = scheduler._calculate_dynamic_penalty(
            current_station_queue=2,
            candidate_station_queue=0,
            num_charging_stations=10
        )
        assert penalty == 5.0  # Should use normal penalty with many stations
    
    def test_dynamic_penalty_congestion_threshold(self):
        """Test that congestion threshold reduces penalty."""
        scenario = create_2_station_scenario()
        scheduler = Scheduler(
            weights={"individual": 2.0, "operator": 1.0, "overall": 1.0}
        )
        scheduler.scenario = scenario
        
        # Test with current station congested (queue > threshold)
        # Note: For 2-station routes, effective congestion threshold is reduced to 2 (50% of 5)
        # So queue=6 > effective_threshold=2, penalty should be reduced
        penalty = scheduler._calculate_dynamic_penalty(
            current_station_queue=6,
            candidate_station_queue=5,
            num_charging_stations=2
        )
        assert penalty == 5.0  # Should reduce penalty by 50%
        
        # Test with current station not congested (queue <= threshold)
        # queue=3 > effective_threshold=2, so penalty still reduced
        penalty = scheduler._calculate_dynamic_penalty(
            current_station_queue=3,
            candidate_station_queue=2,
            num_charging_stations=2
        )
        assert penalty == 5.0  # Should reduce penalty due to few-station route logic
        
        # Test with many stations (normal threshold)
        penalty = scheduler._calculate_dynamic_penalty(
            current_station_queue=3,
            candidate_station_queue=2,
            num_charging_stations=10
        )
        assert penalty == 10.0  # Should use normal penalty with many stations
    
    def test_dynamic_penalty_few_station_route(self):
        """Test that few-station routes use aggressive balancing."""
        scenario = create_2_station_scenario()
        scheduler = Scheduler(
            weights={"individual": 1.0, "operator": 1.0, "overall": 1.0}
        )
        scheduler.scenario = scenario
        
        # Few-station route (2 stations) should use reduced thresholds
        penalty = scheduler._calculate_dynamic_penalty(
            current_station_queue=2,
            candidate_station_queue=0,
            num_charging_stations=2
        )
        assert penalty == 0.0  # Should ignore penalty with reduced threshold (1)
        
        # Many-station route should use normal thresholds
        penalty = scheduler._calculate_dynamic_penalty(
            current_station_queue=2,
            candidate_station_queue=0,
            num_charging_stations=10
        )
        assert penalty == 5.0  # Should use normal penalty
    
    def test_2_station_load_distribution(self):
        """Test that load-aware distributes load across 2 stations."""
        scenario = create_2_station_scenario(num_buses=20)
        scheduler = Scheduler()
        result = scheduler.schedule(scenario)
        
        # Count buses at each station
        station_a_count = 0
        station_b_count = 0
        
        for bus_schedule in result.bus_schedules:
            for event in bus_schedule.charging_events:
                if event.station_id == "A":
                    station_a_count += 1
                elif event.station_id == "B":
                    station_b_count += 1
        
        # Both stations should have buses (not all at one station)
        assert station_a_count > 0, "Station A should have buses"
        assert station_b_count > 0, "Station B should have buses"
        
        # Load should be reasonably balanced (not 20 vs 0)
        # Allow some imbalance but not extreme
        max_queue = max(station_a_count, station_b_count)
        min_queue = min(station_a_count, station_b_count)
        assert max_queue - min_queue <= 12, f"Load imbalance too high: {max_queue} vs {min_queue}"
    
    def test_3_station_load_distribution(self):
        """Test that load-aware distributes load across 3 stations."""
        scenario = create_3_station_scenario(num_buses=20)
        scheduler = Scheduler()
        result = scheduler.schedule(scenario)
        
        # Count buses at each station
        station_counts = {"A": 0, "B": 0, "C": 0}
        
        for bus_schedule in result.bus_schedules:
            for event in bus_schedule.charging_events:
                if event.station_id in station_counts:
                    station_counts[event.station_id] += 1
        
        # All stations should have some buses
        for station, count in station_counts.items():
            assert count > 0, f"Station {station} should have buses"
        
        # Load should be distributed (not all at one station)
        max_queue = max(station_counts.values())
        min_queue = min(station_counts.values())
        assert max_queue - min_queue <= 10, f"Load imbalance too high: {max_queue} vs {min_queue}"
    
    def test_queue_threshold_from_config(self):
        """Test that queue_threshold can be set via scenario config."""
        scenario = create_2_station_scenario()
        # Set queue_threshold in world_config (this is now derived from operator weight)
        scenario.world_config.__dict__['queue_threshold'] = 5
        
        scheduler = Scheduler()
        assert scheduler.queue_threshold == 3  # Initial value from default weights
        
        scheduler.schedule(scenario)
        # Config override should work (queue_threshold gets set from world_config)
        assert scheduler.queue_threshold == 5  # Should be overridden from config
    
    def test_congestion_threshold_from_config(self):
        """Test that congestion_threshold can be set via scenario config."""
        scenario = create_2_station_scenario()
        # Set congestion_threshold in world_config (this is now derived from overall weight)
        scenario.world_config.__dict__['congestion_threshold'] = 10
        
        scheduler = Scheduler()
        assert scheduler.congestion_threshold == 3  # Initial value from default weights
        
        scheduler.schedule(scenario)
        # Config override should work (congestion_threshold gets set from world_config)
        assert scheduler.congestion_threshold == 10  # Should be overridden from config
    
    def test_queue_threshold_zero(self):
        """Test with queue_threshold=0 (always aggressive)."""
        scenario = create_2_station_scenario()
        scheduler = Scheduler()
        # Set queue_threshold in config to 0
        scenario.world_config.__dict__['queue_threshold'] = 0
        
        # Run schedule to apply config override
        scheduler.schedule(scenario)
        
        # With threshold=0, any queue difference should trigger penalty reduction
        # Use many stations to avoid few-station logic overriding
        penalty = scheduler._calculate_dynamic_penalty(
            current_station_queue=1,
            candidate_station_queue=0,
            num_charging_stations=10
        )
        assert penalty == 0.0  # Should ignore penalty even with queue_diff=1
    
    def test_congestion_threshold_very_high(self):
        """Test with congestion_threshold=100 (never triggered)."""
        scenario = create_2_station_scenario()
        scheduler = Scheduler()
        # Set very high thresholds in config
        scenario.world_config.__dict__['congestion_threshold'] = 100
        scenario.world_config.__dict__['queue_threshold'] = 20
        
        # Run schedule to apply config overrides
        scheduler.schedule(scenario)
        
        # With very high thresholds, both congestion and queue diff should not trigger
        # Use many stations to avoid few-station logic overriding
        penalty = scheduler._calculate_dynamic_penalty(
            current_station_queue=10,
            candidate_station_queue=5,  # queue_diff=5, which is < queue_threshold=20
            num_charging_stations=10
        )
        assert penalty == 5.0  # Should use normal penalty (derived from default individual weight)
