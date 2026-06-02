"""
Test dynamic bus generation functionality.
"""

import sys
sys.path.insert(0, '.')

from src.utils import generate_dynamic_buses
from src.utils import minutes_to_time

print("=" * 80)
print("TESTING DYNAMIC BUS GENERATION")
print("=" * 80)
print()

# Test 1: Default configuration (10F/10R, 19:00 start, 15 min interval)
print("Test 1: Default Configuration")
print("-" * 80)
buses = generate_dynamic_buses(
    num_forward=10,
    num_reverse=10,
    start_time_forward="19:00",
    start_time_reverse="19:00",
    interval_minutes=15
)

print(f"Total buses generated: {len(buses)}")
print(f"Forward buses: {len([b for b in buses if b.direction == 'BK'])}")
print(f"Reverse buses: {len([b for b in buses if b.direction == 'KB'])}")
print()

print("First 3 forward buses:")
for bus in buses[:3]:
    print(f"  {bus.id}: {bus.operator}, {bus.direction}, {minutes_to_time(bus.departure_time_minutes)}")

print()
print("First 3 reverse buses:")
for bus in buses[10:13]:
    print(f"  {bus.id}: {bus.operator}, {bus.direction}, {minutes_to_time(bus.departure_time_minutes)}")

print()

# Test 2: Custom configuration (5F/3R, 18:00 start, 10 min interval)
print("Test 2: Custom Configuration (5F/3R, 18:00 start, 10 min interval)")
print("-" * 80)
buses = generate_dynamic_buses(
    num_forward=5,
    num_reverse=3,
    start_time_forward="18:00",
    start_time_reverse="18:00",
    interval_minutes=10
)

print(f"Total buses generated: {len(buses)}")
print(f"Forward buses: {len([b for b in buses if b.direction == 'BK'])}")
print(f"Reverse buses: {len([b for b in buses if b.direction == 'KB'])}")
print()

print("All buses:")
for bus in buses:
    print(f"  {bus.id}: {bus.operator}, {bus.direction}, {minutes_to_time(bus.departure_time_minutes)}")

print()

# Test 3: Verify operator round-robin
print("Test 3: Verify Operator Round-Robin Assignment")
print("-" * 80)
buses = generate_dynamic_buses(
    num_forward=10,
    num_reverse=10,
    start_time_forward="19:00",
    start_time_reverse="19:00",
    interval_minutes=15
)

forward_operators = [b.operator for b in buses if b.direction == 'BK']
print("Forward bus operators:", forward_operators)
print("Expected pattern: kpn, freshbus, flixbus, kpn, freshbus, flixbus...")
print("Pattern matches:", forward_operators == ['kpn', 'freshbus', 'flixbus'] * 3 + ['kpn'])
print()

# Test 4: Verify departure time calculation
print("Test 4: Verify Departure Time Calculation")
print("-" * 80)
buses = generate_dynamic_buses(
    num_forward=5,
    num_reverse=5,
    start_time_forward="19:00",
    start_time_reverse="19:00",
    interval_minutes=15
)

forward_buses = [b for b in buses if b.direction == 'BK']
print("Forward bus departure times:")
for i, bus in enumerate(forward_buses):
    expected_time = minutes_to_time(19*60 + i*15)
    actual_time = minutes_to_time(bus.departure_time_minutes)
    match = "PASS" if expected_time == actual_time else "FAIL"
    print(f"  {bus.id}: {actual_time} (expected: {expected_time}) {match}")

print()

print("=" * 80)
print("TEST COMPLETE")
print("=" * 80)
