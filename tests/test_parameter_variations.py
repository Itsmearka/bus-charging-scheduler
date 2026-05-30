"""
Test runner for parameter variations across scenarios.

This test suite runs scenarios with various parameter combinations
(battery range, charging time, travel speed, chargers per station).
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from .test_helpers import run_scenario_with_params, save_output, print_output


class TestParameterVariations:
    """Test runner for parameter variations."""
    
    def test_battery_range_variations_scenario1(self):
        """Test scenario 1 with battery range variations."""
        scenario_name = "scenario_1_even_spacing"
        battery_ranges = [200, 240, 280]
        
        for battery_range in battery_ranges:
            scenario, result = run_scenario_with_params(
                scenario_name,
                battery_range_km=battery_range
            )
            assert result is not None
            
            filename = f"{scenario_name}_battery_{battery_range}"
            save_output(result, "json", filename, scenario_name, scenario)
            print(f"\n=== {scenario_name} (Battery: {battery_range} km) ===")
            print_output(result, "text")
    
    def test_battery_range_variations_scenario2(self):
        """Test scenario 2 with battery range variations."""
        scenario_name = "scenario_2_bunched_start"
        battery_ranges = [200, 240, 280]
        
        for battery_range in battery_ranges:
            scenario, result = run_scenario_with_params(
                scenario_name,
                battery_range_km=battery_range
            )
            assert result is not None
            
            filename = f"{scenario_name}_battery_{battery_range}"
            save_output(result, "json", filename, scenario_name, scenario)
            print(f"\n=== {scenario_name} (Battery: {battery_range} km) ===")
            print_output(result, "text")
    
    def test_charging_time_variations(self):
        """Test scenario 1 with charging time variations."""
        scenario_name = "scenario_1_even_spacing"
        charging_times = [15, 25, 35]
        
        for charging_time in charging_times:
            scenario, result = run_scenario_with_params(
                scenario_name,
                charging_time_min=charging_time
            )
            assert result is not None
            
            filename = f"{scenario_name}_charging_{charging_time}"
            save_output(result, "json", filename, scenario_name, scenario)
            print(f"\n=== {scenario_name} (Charging: {charging_time} min) ===")
            print_output(result, "text")
    
    def test_travel_speed_variations(self):
        """Test scenario 1 with travel speed variations."""
        scenario_name = "scenario_1_even_spacing"
        travel_speeds = [40, 60, 80]
        
        for travel_speed in travel_speeds:
            scenario, result = run_scenario_with_params(
                scenario_name,
                travel_speed_kmh=travel_speed
            )
            assert result is not None
            
            filename = f"{scenario_name}_speed_{travel_speed}"
            save_output(result, "json", filename, scenario_name, scenario)
            print(f"\n=== {scenario_name} (Speed: {travel_speed} km/h) ===")
            print_output(result, "text")
    
    def test_chargers_per_station_variations(self):
        """Test scenario 1 with chargers per station variations."""
        scenario_name = "scenario_1_even_spacing"
        charger_counts = [1, 2, 5]
        
        for chargers in charger_counts:
            scenario, result = run_scenario_with_params(
                scenario_name,
                chargers_per_station=chargers
            )
            assert result is not None
            
            filename = f"{scenario_name}_chargers_{chargers}"
            save_output(result, "json", filename, scenario_name, scenario)
            print(f"\n=== {scenario_name} (Chargers: {chargers}) ===")
            print_output(result, "text")
    
    def test_combined_parameter_variations(self):
        """Test scenario 1 with combined parameter variations."""
        scenario_name = "scenario_1_even_spacing"
        
        # Test low battery + high speed
        scenario, result = run_scenario_with_params(
            scenario_name,
            battery_range_km=200,
            travel_speed_kmh=80
        )
        assert result is not None
        filename = f"{scenario_name}_low_battery_high_speed"
        save_output(result, "json", filename, scenario_name, scenario)
        print(f"\n=== {scenario_name} (Low Battery + High Speed) ===")
        print_output(result, "text")
        
        # Test high battery + low speed
        scenario, result = run_scenario_with_params(
            scenario_name,
            battery_range_km=280,
            travel_speed_kmh=40
        )
        assert result is not None
        filename = f"{scenario_name}_high_battery_low_speed"
        save_output(result, "json", filename, scenario_name, scenario)
        print(f"\n=== {scenario_name} (High Battery + Low Speed) ===")
        print_output(result, "text")
        
        # Test high chargers + low charging time
        scenario, result = run_scenario_with_params(
            scenario_name,
            chargers_per_station=5,
            charging_time_min=15
        )
        assert result is not None
        filename = f"{scenario_name}_high_chargers_low_charging"
        save_output(result, "json", filename, scenario_name, scenario)
        print(f"\n=== {scenario_name} (High Chargers + Low Charging) ===")
        print_output(result, "text")
