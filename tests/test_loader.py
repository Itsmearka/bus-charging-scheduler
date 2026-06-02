"""
Unit tests for scenario loader.
"""

import pytest
from src.loader import load_scenario, get_scenario_config, list_available_scenarios, load_scenario_by_name


def test_load_scenario_1():
    """Test loading scenario 1 from JSON file."""
    scenario = load_scenario("data/scenarios/scenario_1_even_spacing.json")
    
    assert scenario.name == "Scenario 1 - Even Spacing"
    assert len(scenario.buses) == 20
    assert scenario.weights == {"individual": 1.0, "operator": 1.0, "overall": 1.0}


def test_load_scenario_4_weights():
    """Test that scenario 4 has custom weights."""
    scenario = load_scenario("data/scenarios/scenario_4_operator_heavy.json")
    
    assert scenario.weights["operator"] == 2.0


def test_load_scenario_bus_departure_conversion():
    """Test that departure times are converted from strings to minutes."""
    scenario = load_scenario("data/scenarios/scenario_1_even_spacing.json")
    
    # First bus departs at 19:00 = 1140 minutes
    first_bus = scenario.buses[0]
    assert first_bus.departure_time_minutes == 1140
    
    # Second bus departs at 19:15 = 1155 minutes
    second_bus = scenario.buses[1]
    assert second_bus.departure_time_minutes == 1155


def test_load_scenario_not_found():
    """Test that loading non-existent scenario raises error."""
    with pytest.raises(FileNotFoundError):
        load_scenario("data/scenarios/non_existent.json")


def test_get_scenario_config():
    """Test getting effective configuration for a scenario."""
    scenario = load_scenario("data/scenarios/scenario_1_even_spacing.json")
    config = get_scenario_config(scenario)
    
    assert config['battery_range_km'] == 240
    assert config['charging_time_minutes'] == 25
    assert config['bus_speed_kmh'] == 60
    assert config['total_route_distance_km'] == 540
    assert len(config['stations']) == 4


def test_get_scenario_config_with_overrides():
    """Test that scenario overrides are applied."""
    # Create a scenario with overrides
    from src.models import Bus, Scenario
    
    buses = [Bus(id="test", operator="kpn", direction="BK", departure_time_minutes=0)]
    scenario = Scenario(
        name="Test",
        buses=buses,
        weights={"individual": 1.0, "operator": 1.0, "overall": 1.0},
        battery_range_km=300,  # Override
        charging_time_minutes=30  # Override
    )
    
    config = get_scenario_config(scenario)
    
    assert config['battery_range_km'] == 300
    assert config['charging_time_minutes'] == 30


def test_list_available_scenarios():
    """Test listing all available scenario files."""
    scenarios = list_available_scenarios()
    
    assert len(scenarios) == 5
    assert all("scenario_" in s for s in scenarios)
    # Use os.path.normpath to handle Windows vs Unix path separators
    import os
    assert os.path.normpath("data/scenarios/scenario_1_even_spacing.json") in [os.path.normpath(s) for s in scenarios]


def test_load_scenario_by_name():
    """Test loading scenario by name."""
    scenario = load_scenario_by_name("scenario_1_even_spacing")
    
    assert scenario is not None
    assert scenario.name == "Scenario 1 - Even Spacing"


def test_load_scenario_by_name_not_found():
    """Test loading non-existent scenario by name returns None."""
    scenario = load_scenario_by_name("non_existent_scenario")
    
    assert scenario is None


def test_scenario_bus_directions():
    """Test that scenarios have buses in both directions."""
    scenario = load_scenario("data/scenarios/scenario_1_even_spacing.json")
    
    bk_buses = [b for b in scenario.buses if b.direction == 'BK']
    kb_buses = [b for b in scenario.buses if b.direction == 'KB']
    
    assert len(bk_buses) == 10
    assert len(kb_buses) == 10


def test_scenario_operators():
    """Test that scenarios have all three operators."""
    scenario = load_scenario("data/scenarios/scenario_1_even_spacing.json")
    
    operators = set(bus.operator for bus in scenario.buses)
    
    assert operators == {'kpn', 'freshbus', 'flixbus'}
