"""
Test to verify if charging at stations A & C reduces wait times at B & D.
"""

import sys
sys.path.insert(0, '.')

from src.scenario_loader import ScenarioLoader
from src.scheduler import Scheduler

# Load scenario 1
loader = ScenarioLoader('data/scenarios')
scenario = loader.load_scenario('scenario_1_even_spacing')

print('Original Scenario 1 Configuration:')
print(f'Number of buses: {len(scenario.buses)}')
print(f'Number of stations: {len(scenario.stations)}')
print(f'Battery range: {scenario.world_config.battery_range_km} km')

# Calculate route distances
route = list(scenario.routes.values())[0]
total_distance = sum(s.distance_km for s in route.segments)
print(f'Total route distance: {total_distance} km')

print('\nRoute segments:')
for i, segment in enumerate(route.segments):
    print(f'  {segment.from_station} -> {segment.to_station}: {segment.distance_km} km')

print('\nCurrent charging logic: Only charges when necessary to reach next station')
print('This results in charging only at B and D for the 540km route with 240km range')

# Run scheduler with current logic
print('\nRunning scheduler with current logic...')
scheduler = Scheduler()
result = scheduler.schedule(scenario)

print(f'\nResults with current logic:')
print(f'Total network time: {result.metrics.total_network_time:.2f} minutes')
print(f'Average wait per bus: {result.metrics.avg_wait_per_bus:.2f} minutes')
print(f'Max wait time: {result.metrics.max_wait_time:.2f} minutes')

# Count buses per station
print('\nCharging distribution with current logic:')
for station_schedule in result.station_schedules:
    print(f'  Station {station_schedule.station_id}: {len(station_schedule.charging_queue)} buses charged')

print('\nObservation: Stations A and C have 0 buses charged.')
print('This is because the current logic only charges when necessary to reach the next station.')
print('With 240km range, buses can reach B from Bengaluru (220km) without charging.')
print('But they must charge at B to reach D (220km more).')
print('And must charge at D to reach Kochi (100km more).')

print('\nHypothesis: If buses also charged at A and C, it would distribute load')
print('and potentially reduce wait times at B and D.')
print('\nTo implement this, we could:')
print('1. Modify _needs_charging to consider load balancing')
print('2. Add a "charge at every station" option')
print('3. Add a rule that prefers less crowded stations')
