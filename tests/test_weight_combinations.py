"""
Test runner for weight matrix combinations across scenarios.

This test suite runs scenarios with various weight combinations
(individual, operator, overall) to test optimization behavior.
"""

import pytest
import sys
from pathlib import Path
from itertools import product

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from .test_helpers import run_scenario_with_params, save_output, print_output


class TestWeightCombinations:
    """Test runner for weight matrix combinations."""
    
    def test_individual_weight_matrix_scenario1(self):
        """Test scenario 1 with individual weight matrix (5 values)."""
        scenario_name = "scenario_1_even_spacing"
        individual_weights = [0.0, 0.5, 1.0, 2.0, 5.0]
        
        for individual_weight in individual_weights:
            weights = {
                "individual": individual_weight,
                "operator": 1.0,
                "overall": 1.0
            }
            
            scenario, result = run_scenario_with_params(scenario_name, weights=weights)
            assert result is not None
            
            filename = f"{scenario_name}_individual_{individual_weight}"
            save_output(result, "json", filename, scenario_name, scenario)
            print(f"\n=== {scenario_name} (Individual: {individual_weight}) ===")
            print_output(result, "text")
    
    def test_operator_weight_matrix_scenario1(self):
        """Test scenario 1 with operator weight matrix (5 values)."""
        scenario_name = "scenario_1_even_spacing"
        operator_weights = [0.0, 0.5, 1.0, 2.0, 5.0]
        
        for operator_weight in operator_weights:
            weights = {
                "individual": 1.0,
                "operator": operator_weight,
                "overall": 1.0
            }
            
            scenario, result = run_scenario_with_params(scenario_name, weights=weights)
            assert result is not None
            
            filename = f"{scenario_name}_operator_{operator_weight}"
            save_output(result, "json", filename, scenario_name, scenario)
            print(f"\n=== {scenario_name} (Operator: {operator_weight}) ===")
            print_output(result, "text")
    
    def test_overall_weight_matrix_scenario1(self):
        """Test scenario 1 with overall weight matrix (5 values)."""
        scenario_name = "scenario_1_even_spacing"
        overall_weights = [0.0, 0.5, 1.0, 2.0, 5.0]
        
        for overall_weight in overall_weights:
            weights = {
                "individual": 1.0,
                "operator": 1.0,
                "overall": overall_weight
            }
            
            scenario, result = run_scenario_with_params(scenario_name, weights=weights)
            assert result is not None
            
            filename = f"{scenario_name}_overall_{overall_weight}"
            save_output(result, "json", filename, scenario_name, scenario)
            print(f"\n=== {scenario_name} (Overall: {overall_weight}) ===")
            print_output(result, "text")
    
    def test_corner_cases_scenario1(self):
        """Test scenario 1 with corner case weight combinations."""
        scenario_name = "scenario_1_even_spacing"
        
        # All zeros (no penalties)
        weights = {"individual": 0.0, "operator": 0.0, "overall": 0.0}
        scenario, result = run_scenario_with_params(scenario_name, weights=weights)
        assert result is not None
        filename = f"{scenario_name}_all_zeros"
        save_output(result, "both", filename, scenario_name, scenario)
        print(f"\n=== {scenario_name} (All Zeros) ===")
        print_output(result, "text")
        
        # All maximums (maximum penalties)
        weights = {"individual": 5.0, "operator": 5.0, "overall": 5.0}
        scenario, result = run_scenario_with_params(scenario_name, weights=weights)
        assert result is not None
        filename = f"{scenario_name}_all_maximums"
        save_output(result, "both", filename, scenario_name, scenario)
        print(f"\n=== {scenario_name} (All Maximums) ===")
        print_output(result, "text")
        
        # High individual, low others (greedy behavior)
        weights = {"individual": 5.0, "operator": 0.1, "overall": 0.1}
        scenario, result = run_scenario_with_params(scenario_name, weights=weights)
        assert result is not None
        filename = f"{scenario_name}_high_individual_low_others"
        save_output(result, "json", filename, scenario_name, scenario)
        print(f"\n=== {scenario_name} (High Individual, Low Others) ===")
        print_output(result, "text")
        
        # Low individual, high others (load balancing behavior)
        weights = {"individual": 0.1, "operator": 5.0, "overall": 5.0}
        scenario, result = run_scenario_with_params(scenario_name, weights=weights)
        assert result is not None
        filename = f"{scenario_name}_low_individual_high_others"
        save_output(result, "json", filename, scenario_name, scenario)
        print(f"\n=== {scenario_name} (Low Individual, High Others) ===")
        print_output(result, "text")
    
    def test_weight_matrix_subset_scenario1(self):
        """Test scenario 1 with a subset of weight matrix (2×2×2 = 8 combinations)."""
        scenario_name = "scenario_1_even_spacing"
        
        # Test subset: individual [0.5, 2.0], operator [0.5, 2.0], overall [0.5, 2.0]
        individual_weights = [0.5, 2.0]
        operator_weights = [0.5, 2.0]
        overall_weights = [0.5, 2.0]
        
        for individual, operator, overall in product(individual_weights, operator_weights, overall_weights):
            weights = {
                "individual": individual,
                "operator": operator,
                "overall": overall
            }
            
            scenario, result = run_scenario_with_params(scenario_name, weights=weights)
            assert result is not None
            
            weight_str = f"{individual}-{operator}-{overall}"
            filename = f"{scenario_name}_weights_{weight_str}"
            save_output(result, "json", filename, scenario_name, scenario)
            print(f"\n=== {scenario_name} (Weights: {weight_str}) ===")
            print_output(result, "text")
    
    def test_weight_matrix_subset_scenario2(self):
        """Test scenario 2 with a subset of weight matrix (2×2×2 = 8 combinations)."""
        scenario_name = "scenario_2_bunched_start"
        
        # Test subset: individual [0.5, 2.0], operator [0.5, 2.0], overall [0.5, 2.0]
        individual_weights = [0.5, 2.0]
        operator_weights = [0.5, 2.0]
        overall_weights = [0.5, 2.0]
        
        for individual, operator, overall in product(individual_weights, operator_weights, overall_weights):
            weights = {
                "individual": individual,
                "operator": operator,
                "overall": overall
            }
            
            scenario, result = run_scenario_with_params(scenario_name, weights=weights)
            assert result is not None
            
            weight_str = f"{individual}-{operator}-{overall}"
            filename = f"{scenario_name}_weights_{weight_str}"
            save_output(result, "json", filename, scenario_name, scenario)
            print(f"\n=== {scenario_name} (Weights: {weight_str}) ===")
            print_output(result, "text")
