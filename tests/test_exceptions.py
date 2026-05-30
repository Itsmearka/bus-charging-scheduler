"""
Comprehensive unit tests for exceptions.py

This test suite covers all custom exceptions in exceptions.py
to ensure 100% code coverage from a senior developer perspective.
"""

import pytest
from src.exceptions import (
    SchedulerError,
    ValidationError,
    ScenarioLoadError,
    SchedulingError,
    RangeConstraintViolation,
    ConfigurationError
)


class TestSchedulerError:
    """Test cases for base SchedulerError exception."""
    
    def test_scheduler_error_creation(self):
        """Test SchedulerError creation with message."""
        error = SchedulerError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)
    
    def test_scheduler_error_inheritance(self):
        """Test that SchedulerError inherits from Exception."""
        error = SchedulerError("Test")
        assert isinstance(error, Exception)
    
    def test_scheduler_error_no_message(self):
        """Test SchedulerError with no message."""
        error = SchedulerError()
        assert isinstance(error, Exception)


class TestValidationError:
    """Test cases for ValidationError exception."""
    
    def test_validation_error_creation(self):
        """Test ValidationError creation with message."""
        error = ValidationError("Invalid input")
        assert str(error) == "Invalid input"
    
    def test_validation_error_inheritance(self):
        """Test that ValidationError inherits from SchedulerError."""
        error = ValidationError("Test")
        assert isinstance(error, SchedulerError)
        assert isinstance(error, Exception)
    
    def test_validation_error_with_context(self):
        """Test ValidationError with detailed context."""
        error = ValidationError("Invalid bus_id: must start with 'bus-'")
        assert "bus_id" in str(error)


class TestScenarioLoadError:
    """Test cases for ScenarioLoadError exception."""
    
    def test_scenario_load_error_creation(self):
        """Test ScenarioLoadError creation with message."""
        error = ScenarioLoadError("Failed to load scenario file")
        assert str(error) == "Failed to load scenario file"
    
    def test_scenario_load_error_inheritance(self):
        """Test that ScenarioLoadError inherits from SchedulerError."""
        error = ScenarioLoadError("Test")
        assert isinstance(error, SchedulerError)
        assert isinstance(error, Exception)
    
    def test_scenario_load_error_with_filename(self):
        """Test ScenarioLoadError with filename context."""
        error = ScenarioLoadError("File not found: scenario_1.json")
        assert "scenario_1.json" in str(error)


class TestSchedulingError:
    """Test cases for SchedulingError exception."""
    
    def test_scheduling_error_creation(self):
        """Test SchedulingError creation with message."""
        error = SchedulingError("Failed to generate schedule")
        assert str(error) == "Failed to generate schedule"
    
    def test_scheduling_error_inheritance(self):
        """Test that SchedulingError inherits from SchedulerError."""
        error = SchedulingError("Test")
        assert isinstance(error, SchedulerError)
        assert isinstance(error, Exception)
    
    def test_scheduling_error_with_bus_id(self):
        """Test SchedulingError with bus context."""
        error = SchedulingError("Cannot schedule bus-001: no available chargers")
        assert "bus-001" in str(error)


class TestRangeConstraintViolation:
    """Test cases for RangeConstraintViolation exception."""
    
    def test_range_constraint_violation_creation(self):
        """Test RangeConstraintViolation creation with message."""
        error = RangeConstraintViolation("Bus cannot travel 300km on 240km range")
        assert "300km" in str(error)
        assert "240km" in str(error)
    
    def test_range_constraint_violation_inheritance(self):
        """Test that RangeConstraintViolation inherits from SchedulerError."""
        error = RangeConstraintViolation("Test")
        assert isinstance(error, SchedulerError)
        assert isinstance(error, Exception)
    
    def test_range_constraint_violation_with_details(self):
        """Test RangeConstraintViolation with detailed context."""
        error = RangeConstraintViolation(
            "Bus bus-001 cannot travel from A to B (300km) "
            "without charging (battery range: 240km)"
        )
        assert "bus-001" in str(error)
        assert "A" in str(error)
        assert "B" in str(error)


class TestConfigurationError:
    """Test cases for ConfigurationError exception."""
    
    def test_configuration_error_creation(self):
        """Test ConfigurationError creation with message."""
        error = ConfigurationError("Invalid configuration: battery range must be positive")
        assert str(error) == "Invalid configuration: battery range must be positive"
    
    def test_configuration_error_inheritance(self):
        """Test that ConfigurationError inherits from SchedulerError."""
        error = ConfigurationError("Test")
        assert isinstance(error, SchedulerError)
        assert isinstance(error, Exception)
    
    def test_configuration_error_with_field_name(self):
        """Test ConfigurationError with field context."""
        error = ConfigurationError("Invalid value for 'charging_time': must be positive")
        assert "charging_time" in str(error)


class TestExceptionHierarchy:
    """Test cases for exception hierarchy and relationships."""
    
    def test_all_exceptions_inherit_from_scheduler_error(self):
        """Test that all custom exceptions inherit from SchedulerError."""
        exceptions = [
            ValidationError,
            ScenarioLoadError,
            SchedulingError,
            RangeConstraintViolation,
            ConfigurationError
        ]
        
        for exception_class in exceptions:
            error = exception_class("Test message")
            assert isinstance(error, SchedulerError), f"{exception_class.__name__} should inherit from SchedulerError"
    
    def test_exception_raising_and_catching(self):
        """Test that exceptions can be raised and caught correctly."""
        with pytest.raises(ValidationError) as exc_info:
            raise ValidationError("Test error")
        assert str(exc_info.value) == "Test error"
    
    def test_specific_exception_catching(self):
        """Test catching specific exception types."""
        with pytest.raises(ValidationError):
            raise ValidationError("Test")
        
        with pytest.raises(SchedulerError):
            raise ValidationError("Test")  # ValidationError inherits from SchedulerError
    
    def test_exception_chaining(self):
        """Test exception chaining (raise from)."""
        try:
            try:
                raise ValueError("Original error")
            except ValueError as e:
                raise ValidationError("Validation failed") from e
        except ValidationError as e:
            assert e.__cause__ is not None
            assert isinstance(e.__cause__, ValueError)


class TestExceptionMessages:
    """Test cases for exception message formatting."""
    
    def test_validation_error_with_field_and_value(self):
        """Test ValidationError with field and value context."""
        error = ValidationError(
            "Invalid value for field 'bus_id': 'invalid-001'. "
            "Expected format: 'bus-XXX'"
        )
        assert "bus_id" in str(error)
        assert "invalid-001" in str(error)
    
    def test_scenario_load_error_with_path(self):
        """Test ScenarioLoadError with file path context."""
        error = ScenarioLoadError(
            "Cannot load scenario from path: /invalid/path/scenario.json"
        )
        assert "/invalid/path/" in str(error)
    
    def test_scheduling_error_with_metrics(self):
        """Test SchedulingError with scheduling metrics."""
        error = SchedulingError(
            "Scheduling failed: 5 buses could not be scheduled due to "
            "insufficient charger capacity"
        )
        assert "5 buses" in str(error)
        assert "insufficient charger capacity" in str(error)
