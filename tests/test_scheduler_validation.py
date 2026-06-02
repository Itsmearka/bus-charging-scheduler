"""
Validation tests for scheduler charging behavior.
Ensures buses charge correctly and constraints are enforced.
"""

import pytest
from src.loader import load_scenario
from src.scheduler import BusChargingScheduler


def test_buses_must_charge_minimum_times():
    """Test that buses charge at least minimum required times."""
    scenario = load_scenario("data/scenarios/scenario_1_even_spacing.json")
    scheduler = BusChargingScheduler(scenario, enable_optimizations=False)
    result = scheduler.solve()
    
    assert result.solver_status in ["OPTIMAL", "FEASIBLE"], \
        f"Solver failed with status: {result.solver_status}"
    
    # 540km route with 240km battery requires at least 2 charges
    min_charges = 2
    
    for plan in result.plans:
        assert len(plan.events) >= min_charges, \
            f"Bus {plan.bus_id} has {len(plan.events)} charges, needs >= {min_charges}"


def test_no_overlapping_charges():
    """Test that no two buses charge at same station simultaneously."""
    scenario = load_scenario("data/scenarios/scenario_1_even_spacing.json")
    scheduler = BusChargingScheduler(scenario, enable_optimizations=False)
    result = scheduler.solve()
    
    for station in ['A', 'B', 'C', 'D']:
        events = []
        for plan in result.plans:
            for event in plan.events:
                if event.station_id == station:
                    events.append(event)
        
        # Check all pairs for overlaps
        for i in range(len(events)):
            for j in range(i + 1, len(events)):
                e1, e2 = events[i], events[j]
                
                # No overlap if one ends before other starts
                no_overlap = (e1.end_time_minutes <= e2.start_time_minutes or
                             e2.end_time_minutes <= e1.start_time_minutes)
                
                assert no_overlap, \
                    f"Overlap at {station}: {e1.bus_id} and {e2.bus_id}"


def test_valid_charging_timing():
    """Test all charging events have valid timing."""
    scenario = load_scenario("data/scenarios/scenario_1_even_spacing.json")
    scheduler = BusChargingScheduler(scenario, enable_optimizations=False)
    result = scheduler.solve()
    
    for plan in result.plans:
        for event in plan.events:
            assert event.end_time_minutes > event.start_time_minutes, \
                f"Invalid: end <= start for {event.bus_id} at {event.station_id}"
            assert event.wait_time_minutes >= 0, \
                f"Negative wait for {event.bus_id} at {event.station_id}"
            assert event.start_time_minutes >= event.arrival_time_minutes, \
                f"Start before arrival for {event.bus_id} at {event.station_id}"


def test_route_order_respected():
    """Test buses charge in route order."""
    scenario = load_scenario("data/scenarios/scenario_1_even_spacing.json")
    scheduler = BusChargingScheduler(scenario, enable_optimizations=False)
    result = scheduler.solve()
    
    order_BK = ['A', 'B', 'C', 'D']
    order_KB = ['D', 'C', 'B', 'A']
    
    for plan in result.plans:
        bus = next(b for b in scenario.buses if b.id == plan.bus_id)
        expected = order_BK if bus.direction == 'BK' else order_KB
        
        charged = [e.station_id for e in plan.events]
        
        for i in range(len(charged) - 1):
            idx1 = expected.index(charged[i])
            idx2 = expected.index(charged[i + 1])
            assert idx2 > idx1, f"Out of order: {plan.bus_id} charges {charged}"


def test_all_scenarios_produce_charges():
    """Test all 5 scenarios produce valid charging plans."""
    scenarios = [
        "data/scenarios/scenario_1_even_spacing.json",
        "data/scenarios/scenario_2_bunched_start.json",
        "data/scenarios/scenario_3_asymmetric_load.json",
        "data/scenarios/scenario_4_operator_heavy.json",
        "data/scenarios/scenario_5_worst_case.json"
    ]
    
    for path in scenarios:
        scenario = load_scenario(path)
        scheduler = BusChargingScheduler(scenario, enable_optimizations=False)
        result = scheduler.solve()
        
        assert result.solver_status in ["OPTIMAL", "FEASIBLE"], \
            f"{scenario.name} failed: {result.solver_status}"
        
        for plan in result.plans:
            assert len(plan.events) >= 2, \
                f"{scenario.name}, Bus {plan.bus_id}: only {len(plan.events)} charges"


def test_charging_duration_correct():
    """Test all charges take exactly 25 minutes."""
    scenario = load_scenario("data/scenarios/scenario_1_even_spacing.json")
    scheduler = BusChargingScheduler(scenario, enable_optimizations=False)
    result = scheduler.solve()
    
    expected_duration = 25  # From config
    
    for plan in result.plans:
        for event in plan.events:
            duration = event.end_time_minutes - event.start_time_minutes
            assert duration == expected_duration, \
                f"Wrong duration for {event.bus_id} at {event.station_id}: {duration}min"


def test_total_wait_time_matches_events():
    """Test total wait time equals sum of event wait times."""
    scenario = load_scenario("data/scenarios/scenario_1_even_spacing.json")
    scheduler = BusChargingScheduler(scenario, enable_optimizations=False)
    result = scheduler.solve()
    
    for plan in result.plans:
        calculated = sum(e.wait_time_minutes for e in plan.events)
        assert plan.total_wait_time_minutes == calculated, \
            f"Wait time mismatch for {plan.bus_id}: {plan.total_wait_time_minutes} != {calculated}"
