"""
Test runner for all pre-built scenarios.

This test suite runs all pre-built scenarios with various parameter
combinations and outputs results in both text and JSON formats.
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from .test_helpers import (
    run_scenario_with_params,
    save_output,
    print_output
)


class TestScenarioRunner:
    """Test runner for pre-built scenarios."""
    
    def test_all_scenarios_default(self):
        """Test all 5 scenarios with default parameters."""
        scenarios = [
            "scenario_1_even_spacing",
            "scenario_2_bunched_start",
            "scenario_3_asymmetric_load",
            "scenario_4_operator_heavy",
            "scenario_5_worst_case"
        ]
        
        for scenario_name in scenarios:
            scenario, result = run_scenario_with_params(scenario_name)
            assert result is not None
            assert len(result.bus_schedules) == len(scenario.buses)
            assert result.metrics.total_network_time > 0
            
            # Save output in both formats
            save_output(result, "both", scenario_name, scenario_name, scenario)
            print(f"\n=== {scenario_name} (Default) ===")
            print_output(result, "text")
    
    def test_scenario_1_weight_variations(self):
        """Test scenario 1 with weight matrix variations."""
        scenario_name = "scenario_1_even_spacing"
        
        # Test weight matrix: individual, operator, overall
        weight_combinations = [
            {"individual": 0.0, "operator": 1.0, "overall": 1.0},  # No individual penalty
            {"individual": 5.0, "operator": 1.0, "overall": 1.0},  # High individual penalty
            {"individual": 1.0, "operator": 0.0, "overall": 1.0},  # No operator balancing
            {"individual": 1.0, "operator": 5.0, "overall": 1.0},  # High operator balancing
            {"individual": 1.0, "operator": 1.0, "overall": 0.0},  # No congestion management
            {"individual": 1.0, "operator": 1.0, "overall": 5.0},  # High congestion management
            {"individual": 5.0, "operator": 5.0, "overall": 5.0},  # All maximum
            {"individual": 0.0, "operator": 0.0, "overall": 0.0},  # All minimum
        ]
        
        for i, weights in enumerate(weight_combinations):
            weight_str = f"{weights['individual']}-{weights['operator']}-{weights['overall']}"
            scenario, result = run_scenario_with_params(scenario_name, weights=weights)
            
            # Save output
            filename = f"{scenario_name}_weights_{weight_str}"
            save_output(result, "both", filename, scenario_name, scenario)
            
            print(f"\n=== {scenario_name} (Weights: {weight_str}) ===")
            print_output(result, "text")
    
    def test_scenario_2_weight_variations(self):
        """Test scenario 2 with weight matrix variations."""
        scenario_name = "scenario_2_bunched_start"
        
        # Test key weight combinations
        weight_combinations = [
            {"individual": 1.0, "operator": 1.0, "overall": 1.0},  # Default
            {"individual": 5.0, "operator": 1.0, "overall": 1.0},  # High individual
            {"individual": 1.0, "operator": 5.0, "overall": 1.0},  # High operator
            {"individual": 1.0, "operator": 1.0, "overall": 5.0},  # High overall
        ]
        
        for i, weights in enumerate(weight_combinations):
            weight_str = f"{weights['individual']}-{weights['operator']}-{weights['overall']}"
            scenario, result = run_scenario_with_params(scenario_name, weights=weights)
            
            # Save output
            filename = f"{scenario_name}_weights_{weight_str}"
            save_output(result, "both", filename, scenario_name, scenario)
            
            print(f"\n=== {scenario_name} (Weights: {weight_str}) ===")
            print_output(result, "text")
    
    def test_scenario_3_weight_variations(self):
        """Test scenario 3 with weight matrix variations."""
        scenario_name = "scenario_3_asymmetric_load"
        
        # Test key weight combinations
        weight_combinations = [
            {"individual": 1.0, "operator": 1.0, "overall": 1.0},  # Default
            {"individual": 5.0, "operator": 1.0, "overall": 1.0},  # High individual
            {"individual": 1.0, "operator": 5.0, "overall": 1.0},  # High operator
            {"individual": 1.0, "operator": 1.0, "overall": 5.0},  # High overall
        ]
        
        for i, weights in enumerate(weight_combinations):
            weight_str = f"{weights['individual']}-{weights['operator']}-{weights['overall']}"
            scenario, result = run_scenario_with_params(scenario_name, weights=weights)
            
            # Save output
            filename = f"{scenario_name}_weights_{weight_str}"
            save_output(result, "both", filename, scenario_name, scenario)
            
            print(f"\n=== {scenario_name} (Weights: {weight_str}) ===")
            print_output(result, "text")
    
    def test_scenario_4_weight_variations(self):
        """Test scenario 4 with weight matrix variations (operator-heavy)."""
        scenario_name = "scenario_4_operator_heavy"
        
        # Test key weight combinations
        weight_combinations = [
            {"individual": 1.0, "operator": 1.0, "overall": 1.0},  # Default
            {"individual": 5.0, "operator": 1.0, "overall": 1.0},  # High individual
            {"individual": 1.0, "operator": 5.0, "overall": 1.0},  # High operator
            {"individual": 1.0, "operator": 1.0, "overall": 5.0},  # High overall
        ]
        
        for i, weights in enumerate(weight_combinations):
            weight_str = f"{weights['individual']}-{weights['operator']}-{weights['overall']}"
            scenario, result = run_scenario_with_params(scenario_name, weights=weights)
            
            # Save output
            filename = f"{scenario_name}_weights_{weight_str}"
            save_output(result, "both", filename, scenario_name, scenario)
            
            print(f"\n=== {scenario_name} (Weights: {weight_str}) ===")
            print_output(result, "text")
    
    def test_scenario_5_weight_variations(self):
        """Test scenario 5 with weight matrix variations (worst case)."""
        scenario_name = "scenario_5_worst_case"
        
        # Test key weight combinations
        weight_combinations = [
            {"individual": 1.0, "operator": 1.0, "overall": 1.0},  # Default
            {"individual": 5.0, "operator": 1.0, "overall": 1.0},  # High individual
            {"individual": 1.0, "operator": 5.0, "overall": 1.0},  # High operator
            {"individual": 1.0, "operator": 1.0, "overall": 5.0},  # High overall
        ]
        
        for i, weights in enumerate(weight_combinations):
            weight_str = f"{weights['individual']}-{weights['operator']}-{weights['overall']}"
            scenario, result = run_scenario_with_params(scenario_name, weights=weights)
            
            # Save output
            filename = f"{scenario_name}_weights_{weight_str}"
            save_output(result, "both", filename, scenario_name, scenario)
            
            print(f"\n=== {scenario_name} (Weights: {weight_str}) ===")
            print_output(result, "text")
    
    def test_scenario_1_parameter_variations(self):
        """Test scenario 1 with parameter variations."""
        scenario_name = "scenario_1_even_spacing"
        
        # Battery range variations
        battery_ranges = [200, 240, 280]
        for battery_range in battery_ranges:
            scenario, result = run_scenario_with_params(
                scenario_name,
                battery_range_km=battery_range
            )
            filename = f"{scenario_name}_battery_{battery_range}"
            save_output(result, "json", filename, scenario_name, scenario)
            print(f"\n=== {scenario_name} (Battery: {battery_range} km) ===")
            print_output(result, "text")
        
        # Charging time variations
        charging_times = [15, 25, 35]
        for charging_time in charging_times:
            scenario, result = run_scenario_with_params(
                scenario_name,
                charging_time_min=charging_time
            )
            filename = f"{scenario_name}_charging_{charging_time}"
            save_output(result, "json", filename, scenario_name, scenario)
            print(f"\n=== {scenario_name} (Charging: {charging_time} min) ===")
            print_output(result, "text")
        
        # Travel speed variations
        travel_speeds = [40, 60, 80]
        for travel_speed in travel_speeds:
            scenario, result = run_scenario_with_params(
                scenario_name,
                travel_speed_kmh=travel_speed
            )
            filename = f"{scenario_name}_speed_{travel_speed}"
            save_output(result, "json", filename, scenario_name, scenario)
            print(f"\n=== {scenario_name} (Speed: {travel_speed} km/h) ===")
            print_output(result, "text")
        
        # Chargers per station variations
        charger_counts = [1, 2, 5]
        for chargers in charger_counts:
            scenario, result = run_scenario_with_params(
                scenario_name,
                chargers_per_station=chargers
            )
            filename = f"{scenario_name}_chargers_{chargers}"
            save_output(result, "json", filename, scenario_name, scenario)
            print(f"\n=== {scenario_name} (Chargers: {chargers}) ===")
            print_output(result, "text")
