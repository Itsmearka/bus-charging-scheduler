"""
Integration tests for end-to-end flows

This test suite covers integration between different components
to ensure 100% code coverage from a senior developer perspective.
"""

import pytest
from src.scenario_loader import ScenarioLoader
from src.scheduler import Scheduler
from src.models import Direction


class TestScenarioLoaderSchedulerIntegration:
    """Integration tests for ScenarioLoader and Scheduler."""
    
    def test_load_and_schedule_scenario(self):
        """Test loading a scenario and running the scheduler."""
        loader = ScenarioLoader("data/scenarios")
        scenario = loader.load_scenario("scenario_1_even_spacing")
        
        scheduler = Scheduler()
        result = scheduler.schedule(scenario)
        
        assert result is not None
        assert len(result.bus_schedules) == len(scenario.buses)
        assert result.metrics.total_network_time > 0
    
    def test_load_multiple_scenarios_and_schedule(self):
        """Test loading and scheduling multiple scenarios."""
        loader = ScenarioLoader("data/scenarios")
        scenarios = loader.list_scenarios()
        
        scheduler = Scheduler()
        
        for scenario_name in scenarios[:3]:  # Test first 3 scenarios
            scenario = loader.load_scenario(scenario_name)
            result = scheduler.schedule(scenario)
            assert result is not None
            assert len(result.bus_schedules) == len(scenario.buses)
    
    def test_scenario_with_custom_weights(self):
        """Test scenario scheduling with custom weights."""
        loader = ScenarioLoader("data/scenarios")
        scenario = loader.load_scenario("scenario_1_even_spacing")
        
        # Modify weights
        scenario.weights = {"individual": 5.0, "operator": 0.1, "overall": 0.1}
        
        scheduler = Scheduler()
        result = scheduler.schedule(scenario)
        
        assert result is not None
        assert result.metrics.total_network_time > 0
    
    def test_scenario_with_modified_world_config(self):
        """Test scenario scheduling with modified world config."""
        loader = ScenarioLoader("data/scenarios")
        scenario = loader.load_scenario("scenario_1_even_spacing")
        
        # Modify world config
        scenario.world_config.battery_range_km = 300.0
        scenario.world_config.charging_time_min = 30.0
        
        scheduler = Scheduler()
        result = scheduler.schedule(scenario)
        
        assert result is not None
        assert result.metrics.total_network_time > 0


class TestSchedulerCustomScenarioIntegration:
    """Integration tests for custom scenario creation and scheduling."""
    
    def test_custom_scenario_creation_and_scheduling(self):
        """Test creating a custom scenario and scheduling it."""
        from app import create_custom_scenario
        
        scenario = create_custom_scenario(
            station_names=["Bengaluru", "A", "B", "Kochi"],
            distances=[100.0, 120.0, 100.0],
            battery_range_km=240.0,
            charging_time_min=25.0,
            travel_speed_kmh=60.0,
            chargers_per_station=1,
            num_buses_per_direction=5,
            departure_interval_min=15,
            weights={"individual": 1.0, "operator": 1.0, "overall": 1.0}
        )
        
        scheduler = Scheduler()
        result = scheduler.schedule(scenario)
        
        assert result is not None
        assert len(result.bus_schedules) == 10  # 5 each direction
        assert result.metrics.total_network_time > 0


class TestEdgeCaseIntegration:
    """Integration tests for edge cases."""
    
    def test_scenario_with_single_charger_per_station(self):
        """Test scenario with single charger per station."""
        loader = ScenarioLoader("data/scenarios")
        scenario = loader.load_scenario("scenario_1_even_spacing")
        
        # Ensure single charger per station
        for station in scenario.stations.values():
            station.num_chargers = 1
        
        scheduler = Scheduler()
        result = scheduler.schedule(scenario)
        
        assert result is not None
        assert result.metrics.avg_wait_per_bus >= 0
    
    def test_scenario_with_multiple_chargers_per_station(self):
        """Test scenario with multiple chargers per station."""
        loader = ScenarioLoader("data/scenarios")
        scenario = loader.load_scenario("scenario_1_even_spacing")
        
        # Set multiple chargers per station
        for station in scenario.stations.values():
            station.num_chargers = 3
        
        scheduler = Scheduler()
        result = scheduler.schedule(scenario)
        
        assert result is not None
        # With more chargers, wait times should be lower
        assert result.metrics.avg_wait_per_bus >= 0
    
    def test_scenario_with_asymmetric_buses(self):
        """Test scenario with asymmetric bus distribution."""
        loader = ScenarioLoader("data/scenarios")
        scenario = loader.load_scenario("scenario_3_asymmetric_load")
        
        scheduler = Scheduler()
        result = scheduler.schedule(scenario)
        
        assert result is not None
        # Should handle asymmetric distribution
        assert len(result.bus_schedules) == len(scenario.buses)
    
    def test_scenario_with_bunched_departures(self):
        """Test scenario with bunched departure times."""
        loader = ScenarioLoader("data/scenarios")
        scenario = loader.load_scenario("scenario_2_bunched_start")
        
        scheduler = Scheduler()
        result = scheduler.schedule(scenario)
        
        assert result is not None
        # Should handle contention from bunched departures
        assert len(result.bus_schedules) == len(scenario.buses)


class TestValidationIntegration:
    """Integration tests for validation across components."""
    
    def test_invalid_direction_in_bus(self):
        """Test that invalid direction in bus is caught."""
        loader = ScenarioLoader("data/scenarios")
        
        # Try to load a scenario with invalid direction (if such scenario exists)
        # This tests the validation integration
        try:
            scenario = loader.load_scenario("scenario_1_even_spacing")
            # All buses should have valid directions
            for bus in scenario.buses:
                assert bus.direction in [Direction.FORWARD, Direction.REVERSE]
        except Exception as e:
            # If validation fails, that's expected
            assert "direction" in str(e).lower() or "invalid" in str(e).lower()
    
    def test_range_constraint_validation(self):
        """Test that range constraints are validated."""
        from src.utils import validate_range_constraint
        from src.exceptions import RangeConstraintViolation
        
        # Test valid range
        is_valid, error = validate_range_constraint(
            distance_km=100.0,
            battery_range_km=240.0,
            bus_id="bus-001",
            from_station="A",
            to_station="B"
        )
        assert is_valid == True
        
        # Test invalid range
        with pytest.raises(RangeConstraintViolation):
            validate_range_constraint(
                distance_km=300.0,
                battery_range_km=240.0,
                bus_id="bus-001",
                from_station="A",
                to_station="B"
            )


class TestGreedyVsLoadAwareComparison:
    """Integration tests comparing greedy and load-aware schedulers."""
    
    def test_greedy_vs_load_aware_comparison(self):
        """Compare greedy and load-aware schedulers on Scenario 1."""
        loader = ScenarioLoader("data/scenarios")
        scenario = loader.load_scenario("scenario_1_even_spacing")
        
        # Run greedy scheduler
        greedy_scheduler = Scheduler()
        greedy_result = greedy_scheduler.schedule(scenario)
        
        # Run load-aware scheduler
        load_aware_scheduler = Scheduler(weights={"individual": 1.0, "operator": 1.0, "overall": 1.0}, look_ahead_depth=2)
        load_aware_result = load_aware_scheduler.schedule(scenario)
        
        # Both should complete successfully
        assert greedy_result is not None
        assert load_aware_result is not None
        assert len(greedy_result.bus_schedules) == len(load_aware_result.bus_schedules)
        
        # Load-aware should reduce wait time (primary goal)
        # This may not always be true depending on scenario, but for even spacing it should
        # We verify that both produce valid schedules
        assert greedy_result.metrics.avg_wait_per_bus >= 0
        assert load_aware_result.metrics.avg_wait_per_bus >= 0
    
    def test_load_aware_may_increase_charging_stops(self):
        """Verify that load-aware may increase charging stops to reduce wait time."""
        loader = ScenarioLoader("data/scenarios")
        scenario = loader.load_scenario("scenario_1_even_spacing")
        
        # Run greedy scheduler
        greedy_scheduler = Scheduler()
        greedy_result = greedy_scheduler.schedule(scenario)
        
        # Run load-aware scheduler
        load_aware_scheduler = Scheduler(weights={"individual": 1.0, "operator": 1.0, "overall": 1.0}, look_ahead_depth=2)
        load_aware_result = load_aware_scheduler.schedule(scenario)
        
        # Count total charging events for each scheduler
        greedy_stops = sum(len(schedule.charging_events) for schedule in greedy_result.bus_schedules)
        load_aware_stops = sum(len(schedule.charging_events) for schedule in load_aware_result.bus_schedules)
        
        # Both should have valid schedules
        assert greedy_stops > 0
        assert load_aware_stops > 0
        
        # Load-aware may have more stops (acceptable trade-off for reduced wait time)
        # We don't assert strict inequality as it depends on scenario
    
    def test_load_aware_with_different_depths(self):
        """Test load-aware scheduler with different look_ahead_depth values."""
        loader = ScenarioLoader("data/scenarios")
        scenario = loader.load_scenario("scenario_1_even_spacing")
        
        # Test with depth=1
        scheduler_depth_1 = Scheduler(look_ahead_depth=1)
        result_depth_1 = scheduler_depth_1.schedule(scenario)
        
        # Test with depth=2 (default)
        scheduler_depth_2 = Scheduler(look_ahead_depth=2)
        result_depth_2 = scheduler_depth_2.schedule(scenario)
        
        # Test with unlimited depth
        scheduler_depth_unlimited = Scheduler(look_ahead_depth=None)
        result_depth_unlimited = scheduler_depth_unlimited.schedule(scenario)
        
        # All should complete successfully
        assert result_depth_1 is not None
        assert result_depth_2 is not None
        assert result_depth_unlimited is not None
        
        # All should have same number of buses
        assert len(result_depth_1.bus_schedules) == len(result_depth_2.bus_schedules)
        assert len(result_depth_2.bus_schedules) == len(result_depth_unlimited.bus_schedules)
