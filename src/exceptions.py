"""
Custom exception hierarchy for the Bus Charging Scheduler.

This module defines a structured exception hierarchy for better error handling
and debugging throughout the application.
"""


class SchedulerError(Exception):
    """
    Base exception for all scheduler-related errors.
    
    All custom exceptions in this application inherit from this base class,
    allowing for easy catching of any scheduler-specific error.
    """
    pass


class ValidationError(SchedulerError):
    """
    Raised when input data fails validation.
    
    This exception is used when scenario data, configuration, or other inputs
    do not meet the required constraints or format.
    """
    pass


class ScenarioLoadError(SchedulerError):
    """
    Raised when a scenario file cannot be loaded or parsed.
    
    This exception is used for file I/O errors, JSON parsing errors,
    and other issues related to loading scenario files.
    """
    pass


class SchedulingError(SchedulerError):
    """
    Raised when the scheduling algorithm encounters an unrecoverable error.
    
    This exception is used for errors during the scheduling process,
    such as impossible constraints or invalid state.
    """
    pass


class RangeConstraintViolation(SchedulerError):
    """
    Raised when a bus cannot complete a segment without charging.
    
    This exception is used when the distance between stations exceeds
    the bus's battery range.
    """
    pass


class ConfigurationError(SchedulerError):
    """
    Raised when configuration is invalid or missing required fields.
    
    This exception is used for errors in config.json or scenario configuration.
    """
    pass
