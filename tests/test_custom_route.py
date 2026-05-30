"""
Test script for custom route creation feature.
"""

import sys
sys.path.insert(0, '.')

from src.models import Scenario
from app import create_custom_scenario

def test_custom_scenario_creation():
    """
    Test that custom scenarios can be created correctly.
    """
    print("Testing custom scenario creation...")
    
    # Create a simple custom route
    station_names = ["Bengaluru", "A", "B", "Kochi"]
    distances = [100.0, 120.0, 100.0]
    
    scenario = create_custom_scenario(
        station_names=station_names,
        distances=distances,
        battery_range_km=240.0,
        charging_time_min=25.0,
        travel_speed_kmh=60.0,
        chargers_per_station=1,
        num_buses_per_direction=5,
        departure_interval_min=15,
        weights={
            "individual": 1.0,
            "operator": 1.0,
            "overall": 1.0
        }
    )
    
    # Verify scenario structure
    assert scenario is not None, "Scenario should not be None"
    assert isinstance(scenario, Scenario), "Should return a Scenario object"
    assert scenario.metadata["name"] == "Custom Route", "Scenario name should be 'Custom Route'"
    assert len(scenario.stations) == len(station_names), f"Should have {len(station_names)} stations"
    assert len(scenario.buses) == 10, f"Should have {5*2} buses (5 each direction)"
    
    # Verify stations
    for station_name in station_names:
        assert station_name in scenario.stations, f"Station {station_name} should exist"
        assert scenario.stations[station_name].num_chargers == 1, "Should have 1 charger per station"
    
    # Verify route
    assert "custom_route" in scenario.routes, "Should have custom_route"
    route = scenario.routes["custom_route"]
    assert len(route.segments) == len(distances), f"Should have {len(distances)} segments"
    
    # Verify distances
    for i, segment in enumerate(route.segments):
        assert segment.distance_km == distances[i], f"Segment {i} should have distance {distances[i]}"
    
    print("Custom scenario creation test PASSED!")
    return scenario

def test_custom_scenario_with_scheduler():
    """
    Test that custom scenarios can be scheduled correctly.
    """
    print("\nTesting custom scenario with scheduler...")
    
    from src.scheduler import Scheduler
    
    # Create custom scenario
    scenario = create_custom_scenario(
        station_names=["Bengaluru", "A", "B", "C", "D", "Kochi"],
        distances=[100.0, 120.0, 100.0, 120.0, 100.0],
        battery_range_km=240.0,
        charging_time_min=25.0,
        travel_speed_kmh=60.0,
        chargers_per_station=1,
        num_buses_per_direction=10,
        departure_interval_min=15,
        weights={
            "individual": 1.0,
            "operator": 1.0,
            "overall": 1.0
        }
    )
    
    # Run scheduler
    scheduler = Scheduler()
    result = scheduler.schedule(scenario)
    
    # Verify result
    assert result is not None, "Result should not be None"
    assert len(result.bus_schedules) == 20, "Should have 20 bus schedules"
    assert result.metrics.total_network_time > 0, "Total network time should be positive"
    
    print(f"Schedule completed!")
    print(f"Total network time: {result.metrics.total_network_time:.2f} minutes")
    print(f"Average wait per bus: {result.metrics.avg_wait_per_bus:.2f} minutes")
    print(f"Max wait time: {result.metrics.max_wait_time:.2f} minutes")
    
    print("Custom scenario with scheduler test PASSED!")

if __name__ == "__main__":
    test_custom_scenario_creation()
    test_custom_scenario_with_scheduler()
    print("\nAll custom route tests PASSED!")
