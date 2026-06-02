"""
Unit tests for data models.
"""

import pytest
from src.models import Bus, Station, ChargingEvent, ChargingPlan, Scenario


def test_bus_creation():
    """Test creating a Bus object with valid data."""
    bus = Bus(
        id="bus-BK-01",
        operator="kpn",
        direction="BK",
        departure_time_minutes=1140
    )
    assert bus.id == "bus-BK-01"
    assert bus.operator == "kpn"
    assert bus.direction == "BK"
    assert bus.departure_time_minutes == 1140


def test_bus_invalid_direction():
    """Test that invalid direction raises validation error."""
    with pytest.raises(ValueError, match="Direction must be 'BK' or 'KB'"):
        Bus(
            id="bus-BK-01",
            operator="kpn",
            direction="INVALID",
            departure_time_minutes=1140
        )


def test_bus_invalid_operator():
    """Test that invalid operator raises validation error."""
    with pytest.raises(ValueError, match="Operator must be one of"):
        Bus(
            id="bus-BK-01",
            operator="invalid_operator",
            direction="BK",
            departure_time_minutes=1140
        )


def test_bus_operator_case_insensitive():
    """Test that operator names are converted to lowercase."""
    bus1 = Bus(id="bus-01", operator="KPN", direction="BK", departure_time_minutes=0)
    bus2 = Bus(id="bus-02", operator="kpn", direction="BK", departure_time_minutes=0)
    assert bus1.operator == bus2.operator == "kpn"


def test_station_creation():
    """Test creating a Station object."""
    station = Station(id="A", name="Station A", chargers_count=1, location_km=100)
    assert station.id == "A"
    assert station.chargers_count == 1
    assert station.location_km == 100


def test_charging_event_creation():
    """Test creating a ChargingEvent object."""
    event = ChargingEvent(
        bus_id="bus-BK-01",
        station_id="A",
        arrival_time_minutes=1200,
        start_time_minutes=1205,
        end_time_minutes=1230,
        wait_time_minutes=5
    )
    assert event.bus_id == "bus-BK-01"
    assert event.wait_time_minutes == 5


def test_charging_event_wait_time_validation():
    """Test that wait time is validated against arrival and start times."""
    with pytest.raises(ValueError, match="Wait time.*doesn't match"):
        ChargingEvent(
            bus_id="bus-BK-01",
            station_id="A",
            arrival_time_minutes=1200,
            start_time_minutes=1210,
            end_time_minutes=1230,
            wait_time_minutes=5  # Should be 10, not 5
        )


def test_charging_event_end_time_validation():
    """Test that end time must be after start time."""
    with pytest.raises(ValueError, match="End time.*must be after start time"):
        ChargingEvent(
            bus_id="bus-BK-01",
            station_id="A",
            arrival_time_minutes=1200,
            start_time_minutes=1230,
            end_time_minutes=1200,  # Before start time
            wait_time_minutes=30
        )


def test_charging_plan_creation():
    """Test creating a ChargingPlan object."""
    events = [
        ChargingEvent(
            bus_id="bus-BK-01",
            station_id="A",
            arrival_time_minutes=1200,
            start_time_minutes=1205,
            end_time_minutes=1230,
            wait_time_minutes=5
        )
    ]
    plan = ChargingPlan(
        bus_id="bus-BK-01",
        events=events,
        total_wait_time_minutes=5,
        arrival_time_minutes=1440,
        departure_time_minutes=1140
    )
    assert plan.bus_id == "bus-BK-01"
    assert len(plan.events) == 1
    assert plan.total_wait_time_minutes == 5


def test_charging_plan_total_wait_validation():
    """Test that total wait time matches sum of event wait times."""
    events = [
        ChargingEvent(
            bus_id="bus-BK-01",
            station_id="A",
            arrival_time_minutes=1200,
            start_time_minutes=1205,
            end_time_minutes=1230,
            wait_time_minutes=5
        ),
        ChargingEvent(
            bus_id="bus-BK-01",
            station_id="B",
            arrival_time_minutes=1300,
            start_time_minutes=1310,
            end_time_minutes=1335,
            wait_time_minutes=10
        )
    ]
    with pytest.raises(ValueError, match="Total wait.*doesn't match sum of events"):
        ChargingPlan(
            bus_id="bus-BK-01",
            events=events,
            total_wait_time_minutes=5,  # Should be 15
            arrival_time_minutes=1440,
            departure_time_minutes=1140
        )


def test_scenario_creation():
    """Test creating a Scenario object."""
    buses = [
        Bus(id="bus-BK-01", operator="kpn", direction="BK", departure_time_minutes=1140),
        Bus(id="bus-KB-01", operator="freshbus", direction="KB", departure_time_minutes=1140)
    ]
    weights = {"individual": 1.0, "operator": 1.0, "overall": 1.0}
    
    scenario = Scenario(
        name="Test Scenario",
        description="A test scenario",
        buses=buses,
        weights=weights
    )
    assert scenario.name == "Test Scenario"
    assert len(scenario.buses) == 2


def test_scenario_missing_weight():
    """Test that missing required weight raises validation error."""
    buses = [Bus(id="bus-BK-01", operator="kpn", direction="BK", departure_time_minutes=1140)]
    weights = {"individual": 1.0, "operator": 1.0}  # Missing "overall"
    
    with pytest.raises(ValueError, match="Missing required weight"):
        Scenario(
            name="Test Scenario",
            buses=buses,
            weights=weights
        )


def test_scenario_negative_weight():
    """Test that negative weight raises validation error."""
    buses = [Bus(id="bus-BK-01", operator="kpn", direction="BK", departure_time_minutes=1140)]
    weights = {"individual": -1.0, "operator": 1.0, "overall": 1.0}
    
    with pytest.raises(ValueError, match="must be non-negative"):
        Scenario(
            name="Test Scenario",
            buses=buses,
            weights=weights
        )


def test_scenario_duplicate_bus_ids():
    """Test that duplicate bus IDs raise validation error."""
    buses = [
        Bus(id="bus-BK-01", operator="kpn", direction="BK", departure_time_minutes=1140),
        Bus(id="bus-BK-01", operator="freshbus", direction="KB", departure_time_minutes=1140)  # Duplicate ID
    ]
    weights = {"individual": 1.0, "operator": 1.0, "overall": 1.0}
    
    with pytest.raises(ValueError, match="Bus IDs must be unique"):
        Scenario(
            name="Test Scenario",
            buses=buses,
            weights=weights
        )


def test_route_mismatched_distance():
    """Test that Route validates total distance matches sum of segments."""
    from src.models import RouteSegment, Route
    
    segments = [
        RouteSegment(from_location="Bengaluru", to_location="A", distance_km=100),
        RouteSegment(from_location="A", to_location="B", distance_km=120),
    ]
    
    # This should fail because total distance (250) doesn't match sum of segments (220)
    with pytest.raises(ValueError, match="Total distance .* doesn't match sum of segments"):
        Route(
            segments=segments,
            total_distance_km=250
        )
