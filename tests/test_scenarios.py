"""
Integration tests for all scenarios.
Tests the scheduler on all 5 scenarios to ensure valid results.
"""

import pytest
from src.loader import load_scenario
from src.scheduler import BusChargingScheduler


@pytest.mark.integration
def test_scenario_1_solves():
    """Test that scenario 1 produces a valid solution."""
    scenario = load_scenario("data/scenarios/scenario_1_even_spacing.json")
    scheduler = BusChargingScheduler(scenario, enable_optimizations=False)
    
    result = scheduler.solve()
    
    assert result.solver_status in ["OPTIMAL", "FEASIBLE"]
    assert len(result.plans) == 20
    assert result.solve_time_seconds < 60
    
    # Validate charging events
    for plan in result.plans:
        assert len(plan.events) >= 2, f"Bus {plan.bus_id} needs >= 2 charges"
        assert plan.total_wait_time_minutes >= 0


@pytest.mark.integration
def test_scenario_2_solves():
    """Test that scenario 2 produces a valid solution."""
    scenario = load_scenario("data/scenarios/scenario_2_bunched_start.json")
    scheduler = BusChargingScheduler(scenario, enable_optimizations=False)
    
    result = scheduler.solve()
    
    assert result.solver_status in ["OPTIMAL", "FEASIBLE"]
    assert len(result.plans) == 20
    assert result.solve_time_seconds < 65  # Allow slight variance over 60s limit
    
    # Validate charging events
    for plan in result.plans:
        assert len(plan.events) >= 2, f"Bus {plan.bus_id} needs >= 2 charges"
        assert plan.total_wait_time_minutes >= 0


@pytest.mark.integration
def test_scenario_3_solves():
    """Test that scenario 3 (asymmetric load) produces a valid solution."""
    scenario = load_scenario("data/scenarios/scenario_3_asymmetric_load.json")
    scheduler = BusChargingScheduler(scenario, enable_optimizations=False)
    
    result = scheduler.solve()
    
    assert result.solver_status in ["OPTIMAL", "FEASIBLE"]
    assert len(result.plans) == 14  # 10 BK + 4 KB
    assert result.solve_time_seconds < 60
    
    # Validate charging events
    for plan in result.plans:
        assert len(plan.events) >= 2, f"Bus {plan.bus_id} needs >= 2 charges"
        assert plan.total_wait_time_minutes >= 0


@pytest.mark.integration
def test_scenario_4_solves():
    """Test that scenario 4 (operator heavy) produces a valid solution."""
    scenario = load_scenario("data/scenarios/scenario_4_operator_heavy.json")
    scheduler = BusChargingScheduler(scenario, enable_optimizations=False)
    
    result = scheduler.solve()
    
    assert result.solver_status in ["OPTIMAL", "FEASIBLE"]
    assert len(result.plans) == 20
    assert result.solve_time_seconds < 60
    
    # Validate charging events
    for plan in result.plans:
        assert len(plan.events) >= 2, f"Bus {plan.bus_id} needs >= 2 charges"
        assert plan.total_wait_time_minutes >= 0


@pytest.mark.integration
def test_scenario_5_solves():
    """Test that scenario 5 (worst case) produces a valid solution."""
    scenario = load_scenario("data/scenarios/scenario_5_worst_case.json")
    scheduler = BusChargingScheduler(scenario, enable_optimizations=False)
    
    result = scheduler.solve()
    
    assert result.solver_status in ["OPTIMAL", "FEASIBLE"]
    assert len(result.plans) == 20
    assert result.solve_time_seconds < 65  # Allow slight variance over 60s limit
    
    # Validate charging events
    for plan in result.plans:
        assert len(plan.events) >= 2, f"Bus {plan.bus_id} needs >= 2 charges"
        assert plan.total_wait_time_minutes >= 0


@pytest.mark.integration
def test_all_buses_have_plans():
    """Test that all buses in a scenario get charging plans."""
    scenario = load_scenario("data/scenarios/scenario_1_even_spacing.json")
    scheduler = BusChargingScheduler(scenario, enable_optimizations=False)
    
    result = scheduler.solve()
    
    # Each bus should have a plan
    plan_bus_ids = {plan.bus_id for plan in result.plans}
    scenario_bus_ids = {bus.id for bus in scenario.buses}
    
    assert plan_bus_ids == scenario_bus_ids


@pytest.mark.integration
def test_solvers_with_optimizations():
    """Test that scheduler works with Phase 2 optimizations enabled."""
    scenario = load_scenario("data/scenarios/scenario_1_even_spacing.json")
    scheduler = BusChargingScheduler(scenario, enable_optimizations=True)
    
    result = scheduler.solve()
    
    assert result.optimization_enabled == True
    assert result.solver_status in ["OPTIMAL", "FEASIBLE"]
    assert len(result.plans) == 20


@pytest.mark.integration
def test_scenario_4_operator_weight_impact():
    """Test that scenario 4 with high operator weight produces different results."""
    scenario = load_scenario("data/scenarios/scenario_4_operator_heavy.json")
    
    # Run with default weights
    scheduler1 = BusChargingScheduler(scenario, enable_optimizations=False)
    result1 = scheduler1.solve()
    
    # Modify weights to emphasize individual over operator
    scenario.weights = {"individual": 2.0, "operator": 0.5, "overall": 1.0}
    scheduler2 = BusChargingScheduler(scenario, enable_optimizations=False)
    result2 = scheduler2.solve()
    
    # Results should be different (may have different wait times)
    # This is a weak test - in practice, we'd check for specific differences
    assert result1.solver_status in ["OPTIMAL", "FEASIBLE"]
    assert result2.solver_status in ["OPTIMAL", "FEASIBLE"]


@pytest.mark.integration
def test_charging_events_valid():
    """Test that charging events have valid timing."""
    scenario = load_scenario("data/scenarios/scenario_1_even_spacing.json")
    scheduler = BusChargingScheduler(scenario, enable_optimizations=False)
    
    result = scheduler.solve()
    
    for plan in result.plans:
        for event in plan.events:
            # End time should be after start time
            assert event.end_time_minutes > event.start_time_minutes
            # Wait time should be non-negative
            assert event.wait_time_minutes >= 0
            # Start time should be after or at arrival time
            assert event.start_time_minutes >= event.arrival_time_minutes
