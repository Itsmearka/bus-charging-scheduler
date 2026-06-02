"""
Test that all charging events are exactly 25 minutes.
"""

import sys
sys.path.insert(0, '.')

from src.loader import load_scenario, list_available_scenarios
from src.scheduler import BusChargingScheduler

print("=" * 80)
print("TESTING CHARGING DURATION - MUST BE 25 MINUTES")
print("=" * 80)
print()

scenario_files = list_available_scenarios()
all_correct = True

for scenario_file in scenario_files:
    print(f"\n{scenario_file}:")
    print("-" * 80)
    
    scenario = load_scenario(scenario_file)
    scheduler = BusChargingScheduler(scenario, enable_optimizations=False, unlimited_time=False)
    result = scheduler.solve()
    
    issues = []
    for plan in result.plans:
        for event in plan.events:
            duration = event.end_time_minutes - event.start_time_minutes
            if duration != 25:
                issues.append(f"{plan.bus_id} at {event.station_id}: {duration} minutes (expected 25)")
    
    if issues:
        print(f"ERROR: Found {len(issues)} issues:")
        for issue in issues:
            print(f"  - {issue}")
        all_correct = False
    else:
        print(f"PASS: All charging events are exactly 25 minutes")

print()
print("=" * 80)
if all_correct:
    print("PASS: ALL SCENARIOS PASSED - Charging duration is always 25 minutes")
else:
    print("FAIL: SOME SCENARIOS FAILED - Charging duration not always 25 minutes")
print("=" * 80)
