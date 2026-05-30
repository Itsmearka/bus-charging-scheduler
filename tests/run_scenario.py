"""
Standalone script to run a specific scenario with optional parameters.

This script allows quick testing of scenarios without pytest, supporting
command-line arguments for customization.
"""

import sys
import argparse
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from test_helpers import (
    run_scenario_with_params,
    save_output,
    print_output
)


def main():
    """Main function to run scenario from command line."""
    parser = argparse.ArgumentParser(
        description="Run a specific scenario with optional parameters"
    )
    
    parser.add_argument(
        "--scenario",
        type=str,
        required=True,
        choices=[
            "scenario_1_even_spacing",
            "scenario_2_bunched_start",
            "scenario_3_asymmetric_load",
            "scenario_4_operator_heavy",
            "scenario_5_worst_case"
        ],
        help="Scenario name to run"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        choices=["text", "json", "both"],
        default="both",
        help="Output format (default: both)"
    )
    
    parser.add_argument(
        "--weights",
        type=str,
        help="Comma-separated weights (individual,operator,overall), e.g., 1.0,2.0,1.0"
    )
    
    parser.add_argument(
        "--battery-range",
        type=float,
        help="Battery range in km"
    )
    
    parser.add_argument(
        "--charging-time",
        type=float,
        help="Charging time in minutes"
    )
    
    parser.add_argument(
        "--travel-speed",
        type=float,
        help="Travel speed in km/h"
    )
    
    parser.add_argument(
        "--chargers",
        type=int,
        help="Chargers per station"
    )
    
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Do not save output to file"
    )
    
    args = parser.parse_args()
    
    # Parse weights if provided
    weights = None
    if args.weights:
        try:
            weight_values = [float(w.strip()) for w in args.weights.split(",")]
            if len(weight_values) != 3:
                raise ValueError("Weights must be 3 comma-separated values")
            weights = {
                "individual": weight_values[0],
                "operator": weight_values[1],
                "overall": weight_values[2]
            }
        except ValueError as e:
            print(f"Error parsing weights: {e}")
            print("Example: --weights 1.0,2.0,1.0")
            sys.exit(1)
    
    # Run scenario with parameters
    scenario, result = run_scenario_with_params(
        args.scenario,
        weights=weights,
        battery_range_km=args.battery_range,
        charging_time_min=args.charging_time,
        travel_speed_kmh=args.travel_speed,
        chargers_per_station=args.chargers
    )
    
    # Print output to terminal
    print(f"\n{'='*60}")
    print(f"Scenario: {args.scenario}")
    print(f"{'='*60}\n")
    print_output(result, args.output)
    
    # Save output to file unless --no-save flag is set
    if not args.no_save:
        save_output(result, args.output, args.scenario, args.scenario, scenario)
    
    print(f"\n{'='*60}")
    print("Scenario execution completed successfully")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
