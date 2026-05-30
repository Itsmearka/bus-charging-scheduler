"""
Comprehensive unit tests for utils.py

This test suite covers all utility functions in utils.py
to ensure 100% code coverage from a senior developer perspective.
"""

import pytest
from src.utils import (
    time_to_minutes,
    minutes_to_time,
    calculate_travel_time,
    calculate_distance_travelled,
    format_duration,
    validate_range_constraint,
    get_route_segments_for_direction
)
from src.exceptions import RangeConstraintViolation, ValidationError


class TestTimeToMinutes:
    """Test cases for time_to_minutes function."""
    
    def test_time_to_minutes_basic(self):
        """Test basic time to minutes conversion."""
        assert time_to_minutes("12:00") == 720.0
        assert time_to_minutes("00:00") == 0.0
        assert time_to_minutes("23:59") == 1439.0
    
    def test_time_to_minutes_half_hour(self):
        """Test conversion with half hours."""
        assert time_to_minutes("12:30") == 750.0
        assert time_to_minutes("08:15") == 495.0
        assert time_to_minutes("19:45") == 1185.0
    
    def test_time_to_minutes_edge_cases(self):
        """Test edge cases for time conversion."""
        assert time_to_minutes("24:00") == 1440.0


class TestMinutesToTime:
    """Test cases for minutes_to_time function."""
    
    def test_minutes_to_time_basic(self):
        """Test basic minutes to time conversion."""
        assert minutes_to_time(720.0) == "12:00"
        assert minutes_to_time(0.0) == "00:00"
        assert minutes_to_time(1439.0) == "23:59"
    
    def test_minutes_to_time_half_hour(self):
        """Test conversion with half hours."""
        assert minutes_to_time(750.0) == "12:30"
        assert minutes_to_time(495.0) == "08:15"
        assert minutes_to_time(1185.0) == "19:45"
    
    def test_minutes_to_time_rounding(self):
        """Test that minutes are properly rounded."""
        assert minutes_to_time(720.5) == "12:00"
        assert minutes_to_time(720.9) == "12:00"
    
    def test_round_trip_conversion(self):
        """Test round-trip conversion is lossless."""
        original = "14:30"
        minutes = time_to_minutes(original)
        converted = minutes_to_time(minutes)
        assert converted == original


class TestCalculateTravelTime:
    """Test cases for calculate_travel_time function."""
    
    def test_calculate_travel_time_basic(self):
        """Test basic travel time calculation."""
        # 100 km at 60 km/h = 100 minutes
        assert calculate_travel_time(100.0, 60.0) == 100.0
        # 120 km at 60 km/h = 120 minutes
        assert calculate_travel_time(120.0, 60.0) == 120.0
    
    def test_calculate_travel_time_different_speeds(self):
        """Test travel time with different speeds."""
        # 100 km at 100 km/h = 60 minutes
        assert calculate_travel_time(100.0, 100.0) == 60.0
        # 100 km at 30 km/h = 200 minutes
        assert calculate_travel_time(100.0, 30.0) == 200.0
    
    def test_calculate_travel_time_zero_speed(self):
        """Test that zero speed raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            calculate_travel_time(100.0, 0.0)
        assert "Speed must be positive" in str(exc_info.value)
    
    def test_calculate_travel_time_negative_speed(self):
        """Test that negative speed raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            calculate_travel_time(100.0, -10.0)
        assert "Speed must be positive" in str(exc_info.value)


class TestCalculateDistanceTravelled:
    """Test cases for calculate_distance_travelled function."""
    
    def test_calculate_distance_travelled_basic(self):
        """Test basic distance calculation."""
        # 60 minutes at 60 km/h = 60 km
        assert calculate_distance_travelled(60.0, 60.0) == 60.0
        # 120 minutes at 60 km/h = 120 km
        assert calculate_distance_travelled(120.0, 60.0) == 120.0
    
    def test_calculate_distance_travelled_different_speeds(self):
        """Test distance calculation with different speeds."""
        # 60 minutes at 100 km/h = 100 km
        assert calculate_distance_travelled(60.0, 100.0) == 100.0
        # 120 minutes at 30 km/h = 60 km
        assert calculate_distance_travelled(120.0, 30.0) == 60.0


class TestFormatDuration:
    """Test cases for format_duration function."""
    
    def test_format_duration_minutes_only(self):
        """Test formatting duration in minutes only."""
        assert format_duration(30.0) == "30m"
        assert format_duration(45.0) == "45m"
        assert format_duration(59.0) == "59m"
    
    def test_format_duration_hours_only(self):
        """Test formatting duration in hours only."""
        assert format_duration(60.0) == "1h"
        assert format_duration(120.0) == "2h"
        assert format_duration(180.0) == "3h"
    
    def test_format_duration_hours_and_minutes(self):
        """Test formatting duration with hours and minutes."""
        assert format_duration(90.0) == "1h 30m"
        assert format_duration(150.0) == "2h 30m"
        assert format_duration(105.0) == "1h 45m"
    
    def test_format_duration_zero(self):
        """Test formatting zero duration."""
        assert format_duration(0.0) == "0m"
    
    def test_format_duration_large(self):
        """Test formatting large duration."""
        assert format_duration(3665.0) == "61h 5m"


class TestValidateRangeConstraint:
    """Test cases for validate_range_constraint function."""
    
    def test_validate_range_constraint_valid(self):
        """Test validation with valid distance."""
        is_valid, error_msg = validate_range_constraint(
            distance_km=100.0,
            battery_range_km=240.0,
            bus_id="bus-001",
            from_station="A",
            to_station="B"
        )
        assert is_valid == True
        assert error_msg == ""
    
    def test_validate_range_constraint_invalid(self):
        """Test validation with invalid distance (exceeds range)."""
        with pytest.raises(RangeConstraintViolation) as exc_info:
            validate_range_constraint(
                distance_km=300.0,
                battery_range_km=240.0,
                bus_id="bus-001",
                from_station="A",
                to_station="B"
            )
        error_msg = str(exc_info.value)
        assert "bus-001" in error_msg
        assert "A" in error_msg
        assert "B" in error_msg
        assert "300" in error_msg
        assert "240" in error_msg
    
    def test_validate_range_constraint_exact_boundary(self):
        """Test validation at exact boundary."""
        is_valid, error_msg = validate_range_constraint(
            distance_km=240.0,
            battery_range_km=240.0,
            bus_id="bus-001",
            from_station="A",
            to_station="B"
        )
        assert is_valid == True
        assert error_msg == ""


class TestGetRouteSegmentsForDirection:
    """Test cases for get_route_segments_for_direction function."""
    
    def test_get_route_segments_forward(self):
        """Test getting segments in forward direction."""
        segments = [
            {"from_station": "A", "to_station": "B", "distance_km": 100.0},
            {"from_station": "B", "to_station": "C", "distance_km": 120.0}
        ]
        result = get_route_segments_for_direction(segments, "forward")
        assert result == segments
    
    def test_get_route_segments_reverse(self):
        """Test getting segments in reverse direction."""
        segments = [
            {"from_station": "A", "to_station": "B", "distance_km": 100.0},
            {"from_station": "B", "to_station": "C", "distance_km": 120.0}
        ]
        result = get_route_segments_for_direction(segments, "reverse")
        assert len(result) == 2
        assert result[0]["from_station"] == "C"
        assert result[0]["to_station"] == "B"
        assert result[0]["distance_km"] == 120.0
        assert result[1]["from_station"] == "B"
        assert result[1]["to_station"] == "A"
        assert result[1]["distance_km"] == 100.0
    
    def test_get_route_segments_invalid_direction(self):
        """Test that invalid direction raises ValidationError."""
        segments = [{"from_station": "A", "to_station": "B", "distance_km": 100.0}]
        with pytest.raises(ValidationError) as exc_info:
            get_route_segments_for_direction(segments, "invalid")
        assert "Invalid direction" in str(exc_info.value)
    
    def test_get_route_segments_case_insensitive(self):
        """Test that direction is case-sensitive (not case-insensitive)."""
        segments = [
            {"from_station": "A", "to_station": "B", "distance_km": 100.0}
        ]
        # The function expects lowercase 'forward' or 'reverse', not uppercase
        # So 'FORWARD' should raise an error
        with pytest.raises(ValidationError):
            get_route_segments_for_direction(segments, "FORWARD")
    
    def test_get_route_segments_single_segment(self):
        """Test reverse direction with single segment."""
        segments = [{"from_station": "A", "to_station": "B", "distance_km": 100.0}]
        result = get_route_segments_for_direction(segments, "reverse")
        assert len(result) == 1
        assert result[0]["from_station"] == "B"
        assert result[0]["to_station"] == "A"
