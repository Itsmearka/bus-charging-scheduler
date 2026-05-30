"""
Standalone script to run a custom route with optional parameters.

This script allows quick testing of custom routes without pytest, supporting
command-line arguments for customization.
"""

import sys
import argparse
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from test_helpers import (
    create_custom_scenario,
    save_output,
    print_output
)
from src.scheduler import Scheduler


def main():
    """Main function to run custom route from command line."""
    parser = argparse.ArgumentParser(
        description="Run a custom route with optional parameters"
    )
    
    parser.add_argument(
        "--stations",
        type=str,
        required=True,
        help="Comma-separated station names (e.g., Bengaluru,A,Kochi)"
    )
    
    parser.add_argument(
        "--distances",
        type=str,
        required=True,
        help="Comma-separated distances between consecutive stations (e.g., 100,120)"
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
        default=240.0,
        help="Battery range in km (default: 240.0)"
    )
    
    parser.add_argument(
        "--charging-time",
        type=float,
        default=25.0,
        help="Charging time in minutes (default: 25.0)"
    )
    
    parser.add_argument(
        "--travel-speed",
        type=float,
        default=60.0,
        help="Travel speed in km/h (default: 60.0)"
    )
    
    parser.add_argument(
        "--chargers",
        type=int,
        default=1,
        help="Chargers per station (default: 1)"
    )
    
    parser.add_argument(
        "--buses",
        type=int,
        default=10,
        help="Number of buses per direction (default: 10)"
    )
    
    parser.add_argument(
        "--departure-interval",
        type=int,
        default=15,
        help="Departure interval in minutes (default: 15)"
    )
    
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Do not save output to file"
    )
    
    args = parser.parse_args()
    
    # Parse stations
    try:
        station_names = [s.strip() for s in args.stations.split(",")]
        if len(station_names) < 2:
            raise ValueError("At least 2 stations required (start and end cities)")
    except ValueError as e:
        print(f"Error parsing stations: {e}")
        print("Example: --stations Bengaluru,A,Kochi")
        sys.exit(1)
    
    # Parse distances
    try:
        distances = [float(d.strip()) for d in args.distances.split(",")]
        if len(distances) != len(station_names) - 1:
            raise ValueError(
                f"Number of distances ({len(distances)}) must be "
                f"one less than number of stations ({len(station_names)})"
            )
    except ValueError as e:
        print(f"Error parsing distances: {e}")
        print("Example: --distances 100,120")
        sys.exit(1)
    
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
    
    # Create custom scenario
    scenario = create_custom_scenario(
        station_names=station_names,
        distances=distances,
        battery_range_km=args.battery_range,
        charging_time_min=args.charging_time,
        travel_speed_kmh=args.travel_speed,
        chargers_per_station=args.chargers,
        num_buses_per_direction=args.buses,
        departure_interval_min=args.departure_interval,
        weights=weights
    )
    
    # Run scheduler
    scheduler = Scheduler()
    result = scheduler.schedule(scenario)
    
    # Print output to terminal
    print(f"\n{'='*60}")
    print(f"Custom Route: {' -> '.join(station_names)}")
    print(f"Distances: {distances}")
    print(f"{'='*60}\n")
    print_output(result, args.output)
    
    # Save output to file unless --no-save flag is set
    if not args.no_save:
        station_str = "_".join(station_names)
        save_output(result, args.output, f"custom_{station_str}", f"custom_{station_str}", scenario)
    
    print(f"\n{'='*60}")
    print("Custom route execution completed successfully")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
