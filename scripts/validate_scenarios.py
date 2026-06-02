"""
Manual validation script for all scenarios.
Runs scheduler on all scenarios and outputs detailed results for human review.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.loader import load_scenario, list_available_scenarios
from src.scheduler import BusChargingScheduler
from src.utils import minutes_to_time


def validate_scenario(scenario_path: str, enable_optimizations: bool = False) -> None:
    """
    Validate a single scenario and print detailed results.
    
    Args:
        scenario_path: Path to scenario JSON file
        enable_optimizations: Whether to use Phase 2 optimizations
    """
    print(f"\n{'='*80}")
    print(f"Validating: {scenario_path}")
    print(f"{'='*80}\n")
    
    # Load scenario
    scenario = load_scenario(scenario_path)
    print(f"Scenario: {scenario.name}")
    print(f"Description: {scenario.description}")
    print(f"Buses: {len(scenario.buses)}")
    print(f"Weights: {scenario.weights}")
    print(f"\nOptimizations enabled: {enable_optimizations}")
    
    # Run scheduler
    print(f"\nRunning scheduler...")
    scheduler = BusChargingScheduler(scenario, enable_optimizations=enable_optimizations)
    
    try:
        result = scheduler.solve()
        
        print(f"\nSolver Status: {result.solver_status}")
        print(f"Solve Time: {result.solve_time_seconds:.2f} seconds")
        print(f"\nMetrics:")
        print(f"  Total Wait Time: {result.total_wait_time_minutes} minutes")
        print(f"  Max Wait Time: {result.max_wait_time_minutes} minutes")
        print(f"  Average Wait Time: {result.average_wait_time_minutes:.2f} minutes")
        
        # Per-bus timetables
        print(f"\n{'='*80}")
        print(f"PER-BUS TIMETABLES")
        print(f"{'='*80}\n")
        
        for plan in sorted(result.plans, key=lambda p: p.bus_id):
            print(f"\nBus: {plan.bus_id}")
            print(f"  Departure: {minutes_to_time(plan.departure_time_minutes)}")
            print(f"  Arrival: {minutes_to_time(plan.arrival_time_minutes)}")
            print(f"  Total Wait: {plan.total_wait_time_minutes} minutes")
            print(f"  Total Trip Time: {plan.arrival_time_minutes - plan.departure_time_minutes} minutes")
            
            if plan.events:
                print(f"  Charging Events:")
                for event in plan.events:
                    print(f"    Station {event.station_id}:")
                    print(f"      Arrival: {minutes_to_time(event.arrival_time_minutes)}")
                    print(f"      Start: {minutes_to_time(event.start_time_minutes)}")
                    print(f"      End: {minutes_to_time(event.end_time_minutes)}")
                    print(f"      Wait: {event.wait_time_minutes} minutes")
            else:
                print(f"  No charging events")
        
        # Per-station queues
        print(f"\n{'='*80}")
        print(f"PER-STATION QUEUES")
        print(f"{'='*80}\n")
        
        stations = ['A', 'B', 'C', 'D']
        for station in stations:
            print(f"\nStation {station}:")
            
            # Collect all charging events at this station
            events_at_station = []
            for plan in result.plans:
                for event in plan.events:
                    if event.station_id == station:
                        events_at_station.append(event)
            
            # Sort by start time
            events_at_station.sort(key=lambda e: e.start_time_minutes)
            
            if events_at_station:
                print(f"  Queue order:")
                for i, event in enumerate(events_at_station, 1):
                    print(f"    {i}. Bus {event.bus_id}")
                    print(f"       Arrival: {minutes_to_time(event.arrival_time_minutes)}")
                    print(f"       Start: {minutes_to_time(event.start_time_minutes)}")
                    print(f"       End: {minutes_to_time(event.end_time_minutes)}")
                    print(f"       Wait: {event.wait_time_minutes} minutes")
            else:
                print(f"  No charging events")
        
        # Operator-level metrics
        print(f"\n{'='*80}")
        print(f"OPERATOR METRICS")
        print(f"{'='*80}\n")
        
        operators = {}
        for plan in result.plans:
            bus_id = plan.bus_id
            # Extract operator from bus_id (format: bus-BK-01, bus-KB-01)
            # Need to get operator from scenario
            bus = next(b for b in scenario.buses if b.id == bus_id)
            operator = bus.operator
            
            if operator not in operators:
                operators[operator] = []
            operators[operator].append(plan)
        
        for operator, plans in operators.items():
            total_wait = sum(p.total_wait_time_minutes for p in plans)
            avg_wait = total_wait / len(plans)
            max_wait = max(p.total_wait_time_minutes for p in plans)
            
            print(f"\nOperator: {operator}")
            print(f"  Buses: {len(plans)}")
            print(f"  Total Wait: {total_wait} minutes")
            print(f"  Average Wait: {avg_wait:.2f} minutes")
            print(f"  Max Wait: {max_wait} minutes")
        
        # Range compliance check
        print(f"\n{'='*80}")
        print(f"RANGE COMPLIANCE CHECK")
        print(f"{'='*80}\n")
        
        from src.utils import validate_range_compliance
        battery_range = 240  # Default from config
        
        for plan in result.plans:
            bus = next(b for b in scenario.buses if b.id == plan.bus_id)
            charging_stations = [event.station_id for event in plan.events]
            
            is_compliant = validate_range_compliance(
                charging_stations, bus.direction, battery_range
            )
            
            status = "COMPLIANT" if is_compliant else "NON-COMPLIANT"
            print(f"Bus {plan.bus_id}: {status}")
            
            if not is_compliant:
                print(f"  WARNING: Bus violates range constraint!")
        
        print(f"\n{'='*80}")
        print(f"VALIDATION COMPLETE")
        print(f"{'='*80}\n")
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main function to validate all scenarios."""
    print("Bus Charging Scheduler - Manual Validation Script")
    print("="*80)
    
    # Get all scenario files
    scenario_files = list_available_scenarios()
    
    print(f"\nFound {len(scenario_files)} scenario files:")
    for scenario_file in scenario_files:
        print(f"  - {scenario_file}")
    
    # Validate each scenario
    for scenario_file in scenario_files:
        validate_scenario(scenario_file, enable_optimizations=False)
    
    print("\n" + "="*80)
    print("ALL SCENARIOS VALIDATED")
    print("="*80)


if __name__ == "__main__":
    main()
