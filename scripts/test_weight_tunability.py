"""
Test weight tunability - verify changing weights produces different schedules.
"""

import sys
sys.path.insert(0, '.')

from src.loader import load_scenario
from src.scheduler import BusChargingScheduler
from src.models import Scenario

print("=" * 80)
print("TESTING WEIGHT TUNABILITY")
print("=" * 80)
print()

# Load Scenario 4 (Operator Heavy)
scenario = load_scenario("data/scenarios/scenario_4_operator_heavy.json")

print("Test 1: Default weights (individual=1.0, operator=1.0, overall=1.0)")
print("-" * 80)
scenario.weights = {'individual': 1.0, 'operator': 1.0, 'overall': 1.0}
scheduler = BusChargingScheduler(scenario, enable_optimizations=False, unlimited_time=False)
result1 = scheduler.solve()
total_wait1 = sum(e.wait_time_minutes for p in result1.plans for e in p.events)
print(f"Total wait time: {total_wait1} minutes")
print(f"Solver status: {result1.solver_status}")
print()

print("Test 2: High operator weight (individual=1.0, operator=2.0, overall=1.0)")
print("-" * 80)
scenario.weights = {'individual': 1.0, 'operator': 2.0, 'overall': 1.0}
scheduler = BusChargingScheduler(scenario, enable_optimizations=False, unlimited_time=False)
result2 = scheduler.solve()
total_wait2 = sum(e.wait_time_minutes for p in result2.plans for e in p.events)
print(f"Total wait time: {total_wait2} minutes")
print(f"Solver status: {result2.solver_status}")
print()

print("Test 3: Low operator weight (individual=1.0, operator=0.5, overall=1.0)")
print("-" * 80)
scenario.weights = {'individual': 1.0, 'operator': 0.5, 'overall': 1.0}
scheduler = BusChargingScheduler(scenario, enable_optimizations=False, unlimited_time=False)
result3 = scheduler.solve()
total_wait3 = sum(e.wait_time_minutes for p in result3.plans for e in p.events)
print(f"Total wait time: {total_wait3} minutes")
print(f"Solver status: {result3.solver_status}")
print()

print("=" * 80)
print("RESULTS:")
print("=" * 80)
print(f"Default weights: {total_wait1} min")
print(f"High operator weight: {total_wait2} min")
print(f"Low operator weight: {total_wait3} min")
print()

if total_wait1 != total_wait2 or total_wait1 != total_wait3:
    print("PASS: Weight changes produce different schedules (as expected)")
else:
    print("WARNING: Weight changes did not produce different schedules (unexpected)")
