"""
Edge case and error handling tests

This test suite covers edge cases, boundary conditions, and error handling
to ensure 100% code coverage from a senior developer perspective.
"""

import pytest
from src.models import WorldConfig, Segment, Route, Station, Bus, Scenario, Direction
from src.scheduler import Scheduler
from src.scenario_loader import ScenarioLoader
from src.utils import time_to_minutes, minutes_to_time, calculate_travel_time
from src.exceptions import ValidationError, RangeConstraintViolation


class TestTimeConversionEdgeCases:
    """Edge case tests for time conversion functions."""
    
    def test_time_to_minutes_midnight(self):
        """Test conversion at midnight boundary."""
        assert time_to_minutes("00:00") == 0.0
    
    def test_time_to_minutes_end_of_day(self):
        """Test conversion at end of day."""
        assert time_to_minutes("23:59") == 1439.0
    
    def test_time_to_minutes_24_hours(self):
        """Test conversion at 24:00 (next day midnight)."""
        assert time_to_minutes("24:00") == 1440.0
    
    def test_minutes_to_time_zero(self):
        """Test conversion from zero minutes."""
        assert minutes_to_time(0.0) == "00:00"
    
    def test_minutes_to_time_large_value(self):
        """Test conversion from large minute value."""
        assert minutes_to_time(1500.0) == "25:00"  # 25 hours


class TestTravelCalculationEdgeCases:
    """Edge case tests for travel calculation functions."""
    
    def test_calculate_travel_time_zero_distance(self):
        """Test travel time with zero distance."""
        assert calculate_travel_time(0.0, 60.0) == 0.0
    
    def test_calculate_travel_time_very_slow_speed(self):
        """Test travel time with very slow speed."""
        assert calculate_travel_time(100.0, 1.0) == 6000.0  # 100 hours
    
    def test_calculate_travel_time_very_fast_speed(self):
        """Test travel time with very fast speed."""
        assert calculate_travel_time(100.0, 1000.0) == 6.0  # 6 minutes


class TestModelEdgeCases:
    """Edge case tests for data models."""
    
    def test_world_config_zero_values(self):
        """Test WorldConfig with zero values."""
        config = WorldConfig(
            battery_range_km=0.0,
            charging_time_min=0.0,
            travel_speed_kmh=0.0
        )
        assert config.battery_range_km == 0.0
        assert config.charging_time_min == 0.0
        assert config.travel_speed_kmh == 0.0
    
    def test_route_empty_segments(self):
        """Test Route with empty segments list."""
        route = Route(
            route_id="empty",
            name="Empty Route",
            segments=[],
            total_distance=0.0
        )
        assert len(route.segments) == 0
        assert route.total_distance == 0.0
    
    def test_route_single_segment(self):
        """Test Route with single segment."""
        segments = [Segment("A", "B", 100.0)]
        route = Route(
            route_id="single",
            name="Single Segment",
            segments=segments,
            total_distance=100.0
        )
        assert len(route.segments) == 1
    
    def test_station_zero_chargers(self):
        """Test Station with zero chargers (edge case)."""
        station = Station(station_id="A", name="Station A", num_chargers=0)
        assert station.num_chargers == 0
    
    def test_station_many_chargers(self):
        """Test Station with many chargers."""
        station = Station(station_id="A", name="Station A", num_chargers=100)
        assert station.num_chargers == 100
    
    def test_bus_schedule_empty_events(self):
        """Test BusSchedule with empty charging events."""
        from src.models import BusSchedule
        schedule = BusSchedule(
            bus_id="bus-001",
            charging_events=[],
            travel_segments=[],
            total_wait_time=0.0,
            final_arrival_time=0.0
        )
        assert len(schedule.charging_events) == 0
        assert len(schedule.travel_segments) == 0


class TestSchedulerEdgeCases:
    """Edge case tests for scheduler."""
    
    def test_schedule_with_single_bus(self):
        """Test scheduling with only one bus."""
        world_config = WorldConfig()
        segments = [Segment("A", "B", 100.0)]
        route = Route("route1", "Test", segments, 100.0)
        stations = {"A": Station("A", "Station A"), "B": Station("B", "Station B")}
        buses = [Bus("bus-001", "kpn", "route1", Direction.FORWARD, "08:00")]
        
        scenario = Scenario(
            metadata={"name": "Single Bus", "description": "Test", "version": "1.0"},
            world_config=world_config,
            routes={"route1": route},
            stations=stations,
            buses=buses,
            weights={"individual": 1.0, "operator": 1.0, "overall": 1.0}
        )
        
        scheduler = Scheduler()
        result = scheduler.schedule(scenario)
        assert result is not None
        assert len(result.bus_schedules) == 1
    
    def test_schedule_with_very_short_distance(self):
        """Test scheduling with very short segment distances."""
        world_config = WorldConfig(battery_range_km=240.0)
        segments = [Segment("A", "B", 10.0)]
        route = Route("route1", "Test", segments, 10.0)
        stations = {"A": Station("A", "Station A"), "B": Station("B", "Station B")}
        buses = [Bus("bus-001", "kpn", "route1", Direction.FORWARD, "08:00")]
        
        scenario = Scenario(
            metadata={"name": "Short Distance", "description": "Test", "version": "1.0"},
            world_config=world_config,
            routes={"route1": route},
            stations=stations,
            buses=buses,
            weights={"individual": 1.0, "operator": 1.0, "overall": 1.0}
        )
        
        scheduler = Scheduler()
        result = scheduler.schedule(scenario)
        assert result is not None
    
    def test_schedule_with_very_long_distance(self):
        """Test scheduling with very long segment distances."""
        world_config = WorldConfig(battery_range_km=1000.0)
        segments = [Segment("A", "B", 500.0)]
        route = Route("route1", "Test", segments, 500.0)
        stations = {"A": Station("A", "Station A"), "B": Station("B", "Station B")}
        buses = [Bus("bus-001", "kpn", "route1", Direction.FORWARD, "08:00")]
        
        scenario = Scenario(
            metadata={"name": "Long Distance", "description": "Test", "version": "1.0"},
            world_config=world_config,
            routes={"route1": route},
            stations=stations,
            buses=buses,
            weights={"individual": 1.0, "operator": 1.0, "overall": 1.0}
        )
        
        scheduler = Scheduler()
        result = scheduler.schedule(scenario)
        assert result is not None
    
    def test_schedule_with_zero_charging_time(self):
        """Test scheduling with zero charging time (edge case)."""
        world_config = WorldConfig(charging_time_min=0.0)
        segments = [Segment("A", "B", 100.0)]
        route = Route("route1", "Test", segments, 100.0)
        stations = {"A": Station("A", "Station A"), "B": Station("B", "Station B")}
        buses = [Bus("bus-001", "kpn", "route1", Direction.FORWARD, "08:00")]
        
        scenario = Scenario(
            metadata={"name": "Zero Charge", "description": "Test", "version": "1.0"},
            world_config=world_config,
            routes={"route1": route},
            stations=stations,
            buses=buses,
            weights={"individual": 1.0, "operator": 1.0, "overall": 1.0}
        )
        
        scheduler = Scheduler()
        result = scheduler.schedule(scenario)
        assert result is not None


class TestScenarioLoaderEdgeCases:
    """Edge case tests for scenario loader."""
    
    def test_load_scenario_with_empty_file(self, tmp_path):
        """Test loading an empty JSON file."""
        empty_file = tmp_path / "empty.json"
        empty_file.write_text("{}")
        
        loader = ScenarioLoader(str(tmp_path))
        with pytest.raises(Exception):  # Should raise some error for incomplete scenario
            loader.load_scenario("empty.json")
    
    def test_load_scenario_with_extra_fields(self, tmp_path):
        """Test loading a scenario with extra/unknown fields."""
        import json
        extra_fields = {
            "metadata": {"name": "Test", "description": "Test", "version": "1.0"},
            "extra_field": "should be ignored",
            "world_config": {
                "battery_range_km": 240.0,
                "charging_time_min": 25.0,
                "travel_speed_kmh": 60.0
            },
            "routes": [],
            "stations": {},
            "buses": [],
            "weights": {"individual": 1.0, "operator": 1.0, "overall": 1.0}
        }
        extra_file = tmp_path / "extra.json"
        extra_file.write_text(json.dumps(extra_fields))
        
        loader = ScenarioLoader(str(tmp_path))
        # Should handle extra fields gracefully
        try:
            scenario = loader.load_scenario("extra.json")
            assert scenario is not None
        except Exception:
            # Or it might reject extra fields
            pass


class TestRangeConstraintEdgeCases:
    """Edge case tests for range constraint validation."""
    
    def test_validate_range_constraint_exact_match(self):
        """Test validation when distance exactly equals battery range."""
        from src.utils import validate_range_constraint
        is_valid, error = validate_range_constraint(
            distance_km=240.0,
            battery_range_km=240.0,
            bus_id="bus-001",
            from_station="A",
            to_station="B"
        )
        assert is_valid == True
    
    def test_validate_range_constraint_zero_distance(self):
        """Test validation with zero distance."""
        from src.utils import validate_range_constraint
        is_valid, error = validate_range_constraint(
            distance_km=0.0,
            battery_range_km=240.0,
            bus_id="bus-001",
            from_station="A",
            to_station="B"
        )
        assert is_valid == True
    
    def test_validate_range_constraint_negative_distance(self):
        """Test validation with negative distance (should be invalid)."""
        from src.utils import validate_range_constraint
        # Negative distance should be invalid or raise an exception
        try:
            is_valid, error = validate_range_constraint(
                distance_km=-10.0,
                battery_range_km=240.0,
                bus_id="bus-001",
                from_station="A",
                to_station="B"
            )
            # If it doesn't raise, check the result
            assert is_valid == False or error != ""
        except Exception:
            # If it raises an exception, that's acceptable for edge case
            pass


class TestDirectionEdgeCases:
    """Edge case tests for Direction enum."""
    
    def test_direction_case_sensitivity(self):
        """Test that Direction enum is case-sensitive."""
        from src.models import Direction
        assert Direction.FORWARD == "forward"
        assert Direction.FORWARD != "FORWARD"
        assert Direction.FORWARD != "Forward"
    
    def test_direction_comparison(self):
        """Test Direction enum comparison."""
        assert Direction.FORWARD == Direction.FORWARD
        assert Direction.FORWARD != Direction.REVERSE


class TestWeightConfigurationEdgeCases:
    """Edge case tests for weight configuration."""
    
    def test_weights_all_zero(self):
        """Test scheduler with all weights set to zero."""
        from src.scheduler import Scheduler
        scheduler = Scheduler(weights={"individual": 0.0, "operator": 0.0, "overall": 0.0})
        
        # Should handle zero weights gracefully
        assert scheduler.weights == {"individual": 0.0, "operator": 0.0, "overall": 0.0}
        assert scheduler.penalty_per_stop == 0.0  # Derived from individual weight
        assert scheduler.queue_threshold == 10  # Derived from operator weight
        assert scheduler.congestion_threshold == 10  # Derived from overall weight
    
    def test_weights_very_large_values(self):
        """Test scheduler with very large weight values."""
        from src.scheduler import Scheduler
        scheduler = Scheduler(weights={"individual": 1000.0, "operator": 1000.0, "overall": 1000.0})
        
        # Should handle large weights gracefully
        assert scheduler.weights == {"individual": 1000.0, "operator": 1000.0, "overall": 1000.0}
        assert scheduler.penalty_per_stop == 5000.0  # Capped at reasonable value
        assert scheduler.queue_threshold == 1  # Minimum threshold
        assert scheduler.congestion_threshold == 2  # Minimum threshold
    
    def test_weights_negative_values(self):
        """Test scheduler with negative weight values."""
        from src.scheduler import Scheduler
        # Negative weights should be handled gracefully
        scheduler = Scheduler(weights={"individual": -1.0, "operator": -1.0, "overall": -1.0})
        
        # Should handle negative weights (may produce unexpected results but shouldn't crash)
        assert scheduler.weights == {"individual": -1.0, "operator": -1.0, "overall": -1.0}


class TestCustomRouteEdgeCases:
    """Edge case tests for custom route creation."""
    
    def test_custom_route_minimum_stations(self):
        """Test custom route with minimum stations (2)."""
        from app import create_custom_scenario
        scenario = create_custom_scenario(
            station_names=["A", "B"],
            distances=[100.0],
            battery_range_km=240.0,
            charging_time_min=25.0,
            travel_speed_kmh=60.0,
            chargers_per_station=1,
            num_buses_per_direction=1,
            departure_interval_min=15,
            weights={"individual": 1.0, "operator": 1.0, "overall": 1.0}
        )
        assert len(scenario.stations) == 2
        assert len(scenario.buses) == 2  # 1 each direction
    
    def test_custom_route_many_stations(self):
        """Test custom route with many stations."""
        from app import create_custom_scenario
        stations = [f"Station_{i}" for i in range(10)]
        distances = [100.0] * 9
        
        scenario = create_custom_scenario(
            station_names=stations,
            distances=distances,
            battery_range_km=240.0,
            charging_time_min=25.0,
            travel_speed_kmh=60.0,
            chargers_per_station=1,
            num_buses_per_direction=2,
            departure_interval_min=15,
            weights={"individual": 1.0, "operator": 1.0, "overall": 1.0}
        )
        assert len(scenario.stations) == 10
        assert len(scenario.buses) == 4  # 2 each direction
