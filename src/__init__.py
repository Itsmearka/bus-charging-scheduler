"""
Bus Charging Scheduler - Public API

This module exports the public API for the Bus Charging Scheduler.
"""

# Core models
from src.models import (
    WorldConfig,
    Segment,
    Route,
    Station,
    Bus,
    ChargingEvent,
    TravelSegment,
    BusSchedule,
    StationSchedule,
    ScheduleMetrics,
    ScheduleResult,
    Scenario,
    Direction
)

# Scenario loader
from src.scenario_loader import ScenarioLoader

# Scheduler
from src.scheduler import Scheduler

# Utilities
from src.utils import (
    time_to_minutes,
    minutes_to_time,
    calculate_travel_time,
    calculate_distance_travelled,
    format_duration,
    validate_range_constraint,
    get_route_segments_for_direction
)

# Exceptions
from src.exceptions import (
    SchedulerError,
    ValidationError,
    ScenarioLoadError,
    SchedulingError,
    RangeConstraintViolation,
    ConfigurationError
)

# Logging configuration
from src.logging_config import setup_logging, get_logger

__all__ = [
    # Models
    "WorldConfig",
    "Segment",
    "Route",
    "Station",
    "Bus",
    "ChargingEvent",
    "TravelSegment",
    "BusSchedule",
    "StationSchedule",
    "ScheduleMetrics",
    "ScheduleResult",
    "Scenario",
    # Enums
    "Direction",
    # Scenario Loader
    "ScenarioLoader",
    # Scheduler
    "Scheduler",
    # Utilities
    "time_to_minutes",
    "minutes_to_time",
    "calculate_travel_time",
    "calculate_distance_travelled",
    "format_duration",
    "validate_range_constraint",
    "get_route_segments_for_direction",
    # Exceptions
    "SchedulerError",
    "ValidationError",
    "ScenarioLoadError",
    "SchedulingError",
    "RangeConstraintViolation",
    "ConfigurationError",
    # Logging
    "setup_logging",
    "get_logger"
]
