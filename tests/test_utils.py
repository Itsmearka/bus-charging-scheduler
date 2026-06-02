"""
Unit tests for utility functions.
"""

import pytest
from src.utils import (
    time_to_minutes,
    minutes_to_time,
    calculate_travel_time,
    get_route_stations_in_order,
    get_station_distance_from_origin,
    calculate_distance_between_stations,
    validate_range_compliance,
    get_segment_distances,
    generate_dynamic_buses
)
from src.models import Bus


def test_time_to_minutes():
    """Test converting time string to minutes."""
    assert time_to_minutes("00:00") == 0
    assert time_to_minutes("01:00") == 60
    assert time_to_minutes("12:30") == 750
    assert time_to_minutes("19:00") == 1140
    assert time_to_minutes("23:59") == 1439


def test_minutes_to_time():
    """Test converting minutes to time string."""
    assert minutes_to_time(0) == "00:00"
    assert minutes_to_time(60) == "01:00"
    assert minutes_to_time(750) == "12:30"
    assert minutes_to_time(1140) == "19:00"
    assert minutes_to_time(1439) == "23:59"


def test_time_conversion_roundtrip():
    """Test that time conversion is reversible."""
    original_time = "19:30"
    minutes = time_to_minutes(original_time)
    converted_back = minutes_to_time(minutes)
    assert converted_back == original_time


def test_calculate_travel_time():
    """Test travel time calculation."""
    assert calculate_travel_time(100, 60) == 100
    assert calculate_travel_time(120, 60) == 120
    assert calculate_travel_time(60, 60) == 60
    assert calculate_travel_time(100, 50) == 120  # 100km at 50km/h = 2 hours = 120 minutes


def test_get_route_stations_in_order_forward():
    """Test getting stations in order for forward direction."""
    stations = get_route_stations_in_order('BK')
    assert stations == ['A', 'B', 'C', 'D']


def test_get_route_stations_in_order_reverse():
    """Test getting stations in order for reverse direction."""
    stations = get_route_stations_in_order('KB')
    assert stations == ['D', 'C', 'B', 'A']


def test_get_route_stations_invalid_direction():
    """Test that invalid direction raises error."""
    with pytest.raises(ValueError, match="Invalid direction"):
        get_route_stations_in_order('INVALID')


def test_get_station_distance_from_origin_forward():
    """Test station distance from origin for forward direction."""
    assert get_station_distance_from_origin('A', 'BK') == 100
    assert get_station_distance_from_origin('B', 'BK') == 220
    assert get_station_distance_from_origin('C', 'BK') == 320
    assert get_station_distance_from_origin('D', 'BK') == 440


def test_get_station_distance_from_origin_reverse():
    """Test station distance from origin for reverse direction."""
    assert get_station_distance_from_origin('D', 'KB') == 100
    assert get_station_distance_from_origin('C', 'KB') == 220
    assert get_station_distance_from_origin('B', 'KB') == 320
    assert get_station_distance_from_origin('A', 'KB') == 440


def test_calculate_distance_between_stations_forward():
    """Test distance calculation between stations in forward direction."""
    assert calculate_distance_between_stations('A', 'B', 'BK') == 120
    assert calculate_distance_between_stations('B', 'C', 'BK') == 100
    assert calculate_distance_between_stations('C', 'D', 'BK') == 120


def test_calculate_distance_between_stations_reverse():
    """Test distance calculation between stations in reverse direction."""
    assert calculate_distance_between_stations('D', 'C', 'KB') == 120
    assert calculate_distance_between_stations('C', 'B', 'KB') == 100
    assert calculate_distance_between_stations('B', 'A', 'KB') == 120


def test_validate_range_compliance_valid():
    """Test range validation with valid charging pattern."""
    # Bengaluru -> A (100km) -> C (200km more) -> Kochi (220km more)
    # All segments within 240km range
    assert validate_range_compliance(['A', 'C'], 'BK', 240) == True


def test_validate_range_compliance_invalid():
    """Test range validation with invalid charging pattern."""
    # Bengaluru -> A (100km) -> Kochi (440km more)
    # A to Kochi is 440km, exceeds 240km range
    assert validate_range_compliance(['A'], 'BK', 240) == False


def test_validate_range_compliance_no_charging():
    """Test range validation with no charging stations."""
    # Entire trip is 540km, exceeds 240km range
    assert validate_range_compliance([], 'BK', 240) == False


def test_validate_range_compliance_no_charging_in_range():
    """Test range validation with no charging when trip is within range."""
    # If battery range is large enough, no charging needed
    assert validate_range_compliance([], 'BK', 600) == True


def test_get_segment_distances_forward():
    """Test getting segment distances for forward direction."""
    segments = get_segment_distances('BK')
    assert len(segments) == 5
    assert segments[0] == ('Bengaluru', 'A', 100)
    assert segments[1] == ('A', 'B', 120)
    assert segments[2] == ('B', 'C', 100)
    assert segments[3] == ('C', 'D', 120)
    assert segments[4] == ('D', 'Kochi', 100)


def test_get_segment_distances_reverse():
    """Test getting segment distances for reverse direction."""
    segments = get_segment_distances('KB')
    assert len(segments) == 5
    assert segments[0] == ('Kochi', 'D', 100)
    assert segments[1] == ('D', 'C', 120)
    assert segments[2] == ('C', 'B', 100)
    assert segments[3] == ('B', 'A', 120)
    assert segments[4] == ('A', 'Bengaluru', 100)


def test_get_segment_distances_invalid():
    """Test that invalid direction raises error."""
    with pytest.raises(ValueError, match="Invalid direction"):
        get_segment_distances('INVALID')


def test_generate_dynamic_buses_basic():
    """Test dynamic bus generation."""
    buses = generate_dynamic_buses(
        num_forward=2,
        num_reverse=2,
        start_time_forward="19:00",
        start_time_reverse="19:00",
        interval_minutes=15
    )
    
    assert len(buses) == 4
    assert buses[0].id == "bus_forward_1"
    assert buses[0].direction == "BK"
    assert buses[0].departure_time_minutes == 1140  # 19:00
    assert buses[1].id == "bus_forward_2"
    assert buses[1].departure_time_minutes == 1155  # 19:15


def test_generate_dynamic_buses_only_forward():
    """Test dynamic bus generation with only forward buses."""
    buses = generate_dynamic_buses(
        num_forward=3,
        num_reverse=0,
        start_time_forward="19:00",
        start_time_reverse="19:00",
        interval_minutes=15
    )
    
    assert len(buses) == 3
    assert all(bus.direction == "BK" for bus in buses)
    assert all("forward" in bus.id for bus in buses)


def test_generate_dynamic_buses_only_reverse():
    """Test dynamic bus generation with only reverse buses."""
    buses = generate_dynamic_buses(
        num_forward=0,
        num_reverse=3,
        start_time_forward="19:00",
        start_time_reverse="19:00",
        interval_minutes=15
    )
    
    assert len(buses) == 3
    assert all(bus.direction == "KB" for bus in buses)
    assert all("reverse" in bus.id for bus in buses)


def test_validate_range_compliance_first_station_out_of_range():
    """Test range validation when first charging station is out of range."""
    # First station is too far from origin
    assert validate_range_compliance(['B'], 'BK', 100) == False


def test_validate_range_compliance_segment_out_of_range():
    """Test range validation when a segment between charges is out of range."""
    # A to C is 200km, which is within 240km range
    # But if we test with smaller range
    assert validate_range_compliance(['A', 'C'], 'BK', 150) == False


def test_get_station_distance_invalid_direction():
    """Test that invalid direction raises ValueError in get_station_distance_from_origin."""
    with pytest.raises(ValueError, match="Invalid direction"):
        get_station_distance_from_origin('A', 'INVALID')
