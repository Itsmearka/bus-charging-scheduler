"""
Test runner for custom route scenarios.

This test suite runs various custom route configurations with different
station counts, distance patterns, and parameter combinations.
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from .test_helpers import (
    create_custom_scenario,
    save_output,
    print_output
)
from src.scheduler import Scheduler


class TestCustomRouteRunner:
    """Test runner for custom route scenarios."""
    
    def test_custom_2_stations(self):
        """Test custom route with 2 stations (minimal)."""
        station_names = ["Bengaluru", "Kochi"]
        distances = [540]
        
        scenario = create_custom_scenario(
            station_names=station_names,
            distances=distances,
            num_buses_per_direction=10
        )
        
        scheduler = Scheduler()
        result = scheduler.schedule(scenario)
        
        assert result is not None
        assert len(result.bus_schedules) == len(scenario.buses)
        
        # Save output
        save_output(result, "both", "custom_2_stations", "custom_2_stations", scenario)
        print("\n=== Custom Route: 2 Stations ===")
        print_output(result, "text")
    
    def test_custom_3_stations(self):
        """Test custom route with 3 stations (small)."""
        station_names = ["Bengaluru", "A", "Kochi"]
        distances = [270, 270]
        
        scenario = create_custom_scenario(
            station_names=station_names,
            distances=distances,
            num_buses_per_direction=10
        )
        
        scheduler = Scheduler()
        result = scheduler.schedule(scenario)
        
        assert result is not None
        assert len(result.bus_schedules) == len(scenario.buses)
        
        # Save output
        save_output(result, "both", "custom_3_stations", "custom_3_stations", scenario)
        print("\n=== Custom Route: 3 Stations ===")
        print_output(result, "text")
    
    def test_custom_4_stations(self):
        """Test custom route with 4 stations (medium)."""
        station_names = ["Bengaluru", "A", "B", "Kochi"]
        distances = [180, 180, 180]
        
        scenario = create_custom_scenario(
            station_names=station_names,
            distances=distances,
            num_buses_per_direction=10
        )
        
        scheduler = Scheduler()
        result = scheduler.schedule(scenario)
        
        assert result is not None
        assert len(result.bus_schedules) == len(scenario.buses)
        
        # Save output
        save_output(result, "both", "custom_4_stations", "custom_4_stations", scenario)
        print("\n=== Custom Route: 4 Stations ===")
        print_output(result, "text")
    
    def test_custom_5_stations(self):
        """Test custom route with 5 stations (large)."""
        station_names = ["Bengaluru", "A", "B", "C", "Kochi"]
        distances = [135, 135, 135, 135]
        
        scenario = create_custom_scenario(
            station_names=station_names,
            distances=distances,
            num_buses_per_direction=10
        )
        
        scheduler = Scheduler()
        result = scheduler.schedule(scenario)
        
        assert result is not None
        assert len(result.bus_schedules) == len(scenario.buses)
        
        # Save output
        save_output(result, "both", "custom_5_stations", "custom_5_stations", scenario)
        print("\n=== Custom Route: 5 Stations ===")
        print_output(result, "text")
    
    def test_custom_6_stations(self):
        """Test custom route with 6 stations (extra large)."""
        station_names = ["Bengaluru", "A", "B", "C", "D", "Kochi"]
        distances = [108, 108, 108, 108, 108]
        
        scenario = create_custom_scenario(
            station_names=station_names,
            distances=distances,
            num_buses_per_direction=10
        )
        
        scheduler = Scheduler()
        result = scheduler.schedule(scenario)
        
        assert result is not None
        assert len(result.bus_schedules) == len(scenario.buses)
        
        # Save output
        save_output(result, "json", "custom_6_stations", "custom_6_stations", scenario)
        print("\n=== Custom Route: 6 Stations ===")
        print_output(result, "text")
    
    def test_custom_equal_distances(self):
        """Test custom route with equal distance pattern."""
        station_names = ["Bengaluru", "A", "B", "C", "Kochi"]
        distances = [135, 135, 135, 135]  # Equal distances
        
        scenario = create_custom_scenario(
            station_names=station_names,
            distances=distances,
            num_buses_per_direction=10
        )
        
        scheduler = Scheduler()
        result = scheduler.schedule(scenario)
        
        assert result is not None
        
        # Save output
        save_output(result, "json", "custom_equal_distances", "custom_equal_distances", scenario)
        print("\n=== Custom Route: Equal Distances ===")
        print_output(result, "text")
    
    def test_custom_increasing_distances(self):
        """Test custom route with increasing distance pattern."""
        station_names = ["Bengaluru", "A", "B", "C", "Kochi"]
        distances = [100, 120, 140, 180]  # Increasing distances
        
        scenario = create_custom_scenario(
            station_names=station_names,
            distances=distances,
            num_buses_per_direction=10
        )
        
        scheduler = Scheduler()
        result = scheduler.schedule(scenario)
        
        assert result is not None
        
        # Save output
        save_output(result, "json", "custom_increasing_distances", "custom_increasing_distances", scenario)
        print("\n=== Custom Route: Increasing Distances ===")
        print_output(result, "text")
    
    def test_custom_decreasing_distances(self):
        """Test custom route with decreasing distance pattern."""
        station_names = ["Bengaluru", "A", "B", "C", "Kochi"]
        distances = [180, 140, 120, 100]  # Decreasing distances
        
        scenario = create_custom_scenario(
            station_names=station_names,
            distances=distances,
            num_buses_per_direction=10
        )
        
        scheduler = Scheduler()
        result = scheduler.schedule(scenario)
        
        assert result is not None
        
        # Save output
        save_output(result, "json", "custom_decreasing_distances", "custom_decreasing_distances", scenario)
        print("\n=== Custom Route: Decreasing Distances ===")
        print_output(result, "text")
    
    def test_custom_random_distances(self):
        """Test custom route with random distance pattern."""
        station_names = ["Bengaluru", "A", "B", "C", "Kochi"]
        distances = [90, 150, 120, 180]  # Random distances
        
        scenario = create_custom_scenario(
            station_names=station_names,
            distances=distances,
            num_buses_per_direction=10
        )
        
        scheduler = Scheduler()
        result = scheduler.schedule(scenario)
        
        assert result is not None
        
        # Save output
        save_output(result, "json", "custom_random_distances", "custom_random_distances", scenario)
        print("\n=== Custom Route: Random Distances ===")
        print_output(result, "text")
    
    def test_custom_5_buses_per_direction(self):
        """Test custom route with 5 buses per direction."""
        station_names = ["Bengaluru", "A", "B", "C", "Kochi"]
        distances = [135, 135, 135, 135]
        
        scenario = create_custom_scenario(
            station_names=station_names,
            distances=distances,
            num_buses_per_direction=5
        )
        
        scheduler = Scheduler()
        result = scheduler.schedule(scenario)
        
        assert result is not None
        assert len(result.bus_schedules) == 10  # 5 forward + 5 reverse
        
        # Save output
        save_output(result, "json", "custom_5_buses", "custom_5_buses", scenario)
        print("\n=== Custom Route: 5 Buses Per Direction ===")
        print_output(result, "text")
    
    def test_custom_20_buses_per_direction(self):
        """Test custom route with 20 buses per direction."""
        station_names = ["Bengaluru", "A", "B", "C", "Kochi"]
        distances = [135, 135, 135, 135]
        
        scenario = create_custom_scenario(
            station_names=station_names,
            distances=distances,
            num_buses_per_direction=20
        )
        
        scheduler = Scheduler()
        result = scheduler.schedule(scenario)
        
        assert result is not None
        assert len(result.bus_schedules) == 40  # 20 forward + 20 reverse
        
        # Save output
        save_output(result, "json", "custom_20_buses", "custom_20_buses", scenario)
        print("\n=== Custom Route: 20 Buses Per Direction ===")
        print_output(result, "text")
    
    def test_custom_30_min_departure_interval(self):
        """Test custom route with 30-minute departure interval."""
        station_names = ["Bengaluru", "A", "B", "C", "Kochi"]
        distances = [135, 135, 135, 135]
        
        scenario = create_custom_scenario(
            station_names=station_names,
            distances=distances,
            num_buses_per_direction=10,
            departure_interval_min=30
        )
        
        scheduler = Scheduler()
        result = scheduler.schedule(scenario)
        
        assert result is not None
        
        # Save output
        save_output(result, "json", "custom_30min_interval", "custom_30min_interval", scenario)
        print("\n=== Custom Route: 30-Min Departure Interval ===")
        print_output(result, "text")
    
    def test_custom_5_min_departure_interval(self):
        """Test custom route with 5-minute departure interval."""
        station_names = ["Bengaluru", "A", "B", "C", "Kochi"]
        distances = [135, 135, 135, 135]
        
        scenario = create_custom_scenario(
            station_names=station_names,
            distances=distances,
            num_buses_per_direction=10,
            departure_interval_min=5
        )
        
        scheduler = Scheduler()
        result = scheduler.schedule(scenario)
        
        assert result is not None
        
        # Save output
        save_output(result, "json", "custom_5min_interval", "custom_5min_interval", scenario)
        print("\n=== Custom Route: 5-Min Departure Interval ===")
        print_output(result, "text")
    
    def test_custom_2_chargers_per_station(self):
        """Test custom route with 2 chargers per station."""
        station_names = ["Bengaluru", "A", "B", "C", "Kochi"]
        distances = [135, 135, 135, 135]
        
        scenario = create_custom_scenario(
            station_names=station_names,
            distances=distances,
            chargers_per_station=2
        )
        
        scheduler = Scheduler()
        result = scheduler.schedule(scenario)
        
        assert result is not None
        
        # Save output
        save_output(result, "json", "custom_2_chargers", "custom_2_chargers", scenario)
        print("\n=== Custom Route: 2 Chargers Per Station ===")
        print_output(result, "text")
    
    def test_custom_5_chargers_per_station(self):
        """Test custom route with 5 chargers per station."""
        station_names = ["Bengaluru", "A", "B", "C", "Kochi"]
        distances = [135, 135, 135, 135]
        
        scenario = create_custom_scenario(
            station_names=station_names,
            distances=distances,
            chargers_per_station=5
        )
        
        scheduler = Scheduler()
        result = scheduler.schedule(scenario)
        
        assert result is not None
        
        # Save output
        save_output(result, "json", "custom_5_chargers", "custom_5_chargers", scenario)
        print("\n=== Custom Route: 5 Chargers Per Station ===")
        print_output(result, "text")
    
    def test_custom_high_individual_weight(self):
        """Test custom route with high individual weight."""
        station_names = ["Bengaluru", "A", "B", "C", "Kochi"]
        distances = [135, 135, 135, 135]
        
        weights = {"individual": 5.0, "operator": 1.0, "overall": 1.0}
        
        scenario = create_custom_scenario(
            station_names=station_names,
            distances=distances,
            weights=weights
        )
        
        scheduler = Scheduler()
        result = scheduler.schedule(scenario)
        
        assert result is not None
        
        # Save output
        save_output(result, "json", "custom_high_individual", "custom_high_individual", scenario)
        print("\n=== Custom Route: High Individual Weight ===")
        print_output(result, "text")
    
    def test_custom_high_operator_weight(self):
        """Test custom route with high operator weight."""
        station_names = ["Bengaluru", "A", "B", "C", "Kochi"]
        distances = [135, 135, 135, 135]
        
        weights = {"individual": 1.0, "operator": 5.0, "overall": 1.0}
        
        scenario = create_custom_scenario(
            station_names=station_names,
            distances=distances,
            weights=weights
        )
        
        scheduler = Scheduler()
        result = scheduler.schedule(scenario)
        
        assert result is not None
        
        # Save output
        save_output(result, "json", "custom_high_operator", "custom_high_operator", scenario)
        print("\n=== Custom Route: High Operator Weight ===")
        print_output(result, "text")
    
    def test_custom_high_overall_weight(self):
        """Test custom route with high overall weight."""
        station_names = ["Bengaluru", "A", "B", "C", "Kochi"]
        distances = [135, 135, 135, 135]
        
        weights = {"individual": 1.0, "operator": 1.0, "overall": 5.0}
        
        scenario = create_custom_scenario(
            station_names=station_names,
            distances=distances,
            weights=weights
        )
        
        scheduler = Scheduler()
        result = scheduler.schedule(scenario)
        
        assert result is not None
        
        # Save output
        save_output(result, "json", "custom_high_overall", "custom_high_overall", scenario)
        print("\n=== Custom Route: High Overall Weight ===")
        print_output(result, "text")
