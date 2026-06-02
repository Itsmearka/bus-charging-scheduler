"""
Deep analysis of all scenarios to verify bus arrival/departure times and station visitation order.
"""

import sys
sys.path.insert(0, '.')

from src.loader import load_scenario, list_available_scenarios
from src.scheduler import BusChargingScheduler
from src.utils import minutes_to_time, get_route_stations_in_order

print("=" * 80)
print("DEEP ANALYSIS OF ALL SCENARIOS")
print("=" * 80)
print()

# Get all scenarios
scenario_files = list_available_scenarios()

for i, scenario_file in enumerate(scenario_files):
    print(f"\n{'=' * 80}")
    print(f"SCENARIO {i + 1}: {scenario_file}")
    print(f"{'=' * 80}")
    print()
    
    # Load scenario
    scenario = load_scenario(scenario_file)
    print(f"Name: {scenario.name}")
    print(f"Description: {scenario.description}")
    print(f"Buses: {len(scenario.buses)}")
    print()
    
    # Run scheduler
    print("Running scheduler...")
    scheduler = BusChargingScheduler(scenario, enable_optimizations=False, unlimited_time=False)
    result = scheduler.solve()
    print(f"Solver status: {result.solver_status}")
    print(f"Solve time: {result.solve_time_seconds:.2f} seconds")
    print()
    
    # Analyze each bus
    print("Analyzing bus schedules...")
    print()
    
    issues_found = []
    
    for plan in result.plans:
        bus = next(b for b in scenario.buses if b.id == plan.bus_id)
        departure_time = minutes_to_time(bus.departure_time_minutes)
        
        print(f"Bus: {plan.bus_id}")
        print(f"  Direction: {bus.direction}")
        print(f"  Departure: {departure_time}")
        print(f"  Operator: {bus.operator}")
        print(f"  Charges at: {[e.station_id for e in plan.events]}")
        
        # Get expected route order
        expected_order = get_route_stations_in_order(bus.direction)
        print(f"  Expected station order: {expected_order}")
        
        # Check actual visitation order
        actual_order = [e.station_id for e in plan.events]
        print(f"  Actual visitation order: {actual_order}")
        
        # Check if order matches
        if actual_order != expected_order:
            # Check if actual order is a subset (bus doesn't visit all stations)
            if set(actual_order).issubset(set(expected_order)):
                # Check if the order is correct for the visited stations
                actual_indices = [expected_order.index(s) for s in actual_order]
                if actual_indices == sorted(actual_indices):
                    print(f"  PASS: Order is correct (subset of route)")
                else:
                    issue = f"Order mismatch: visited {actual_order} but indices {actual_indices} not sorted"
                    print(f"  FAIL: {issue}")
                    issues_found.append((plan.bus_id, issue))
            else:
                issue = f"Invalid station in visitation: {actual_order} not subset of {expected_order}"
                print(f"  FAIL: {issue}")
                issues_found.append((plan.bus_id, issue))
        else:
            print(f"  PASS: Order matches expected route")
        
        # Check arrival times
        print(f"  Arrival times:")
        for event in plan.events:
            arrival_time = minutes_to_time(event.arrival_time_minutes)
            start_time = minutes_to_time(event.start_time_minutes)
            print(f"    Station {event.station_id}: arrive {arrival_time}, start {start_time}, wait {event.wait_time_minutes} min")
        
        # Check if arrival times are logical (after departure)
        for event in plan.events:
            if event.arrival_time_minutes < bus.departure_time_minutes:
                issue = f"Arrival {minutes_to_time(event.arrival_time_minutes)} before departure {departure_time} at station {event.station_id}"
                print(f"  FAIL: {issue}")
                issues_found.append((plan.bus_id, issue))
        
        print()
    
    # Summary
    print(f"Summary for {scenario.name}:")
    if issues_found:
        print(f"  ERROR: Found {len(issues_found)} issues:")
        for bus_id, issue in issues_found:
            print(f"    - {bus_id}: {issue}")
    else:
        print(f"  PASS: No issues found - all bus schedules are logical")
    
    print()

print("=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)
