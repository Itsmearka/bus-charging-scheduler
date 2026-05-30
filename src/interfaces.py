"""
Abstract base classes and interfaces for the Bus Charging Scheduler.

This module defines the contracts for extensibility, following SOLID principles
particularly the Open/Closed Principle (open for extension, closed for modification)
and the Dependency Inversion Principle (depend on abstractions, not concretions).
"""

from abc import ABC, abstractmethod
from typing import Dict, List
from src.models import Scenario, ScheduleResult


class ISchedulingStrategy(ABC):
    """
    Abstract base class for scheduling strategies.
    
    This interface defines the contract for different scheduling algorithms.
    Implementations can include greedy, round-robin, ML-based, etc.
    """
    
    @abstractmethod
    def schedule(self, scenario: Scenario) -> ScheduleResult:
        """
        Execute the scheduling algorithm on a scenario.
        
        Args:
            scenario: The scenario to schedule
            
        Returns:
            ScheduleResult containing the complete schedule and metrics
            
        Raises:
            SchedulingError: If scheduling encounters an unrecoverable error
        """
        pass  # pragma: no cover


class IPriorityCalculator(ABC):
    """
    Abstract base class for priority calculation strategies.
    
    This interface defines the contract for calculating bus priority.
    Different implementations can use different scoring algorithms.
    """
    
    @abstractmethod
    def calculate_priority(
        self,
        bus_id: str,
        current_wait_time: float,
        operator_avg_wait: float,
        progress: float,
        weights: Dict[str, float]
    ) -> float:
        """
        Calculate priority score for a bus.
        
        Args:
            bus_id: Identifier of the bus
            current_wait_time: How long this bus has already waited (minutes)
            operator_avg_wait: Average wait time for this operator's fleet (minutes)
            progress: How far along the bus is in its journey (0-1)
            weights: Optimization weights for different factors
            
        Returns:
            Priority score (higher = higher priority)
        """
        pass  # pragma: no cover


class IRuleEngine(ABC):
    """
    Abstract base class for rule engines.
    
    This interface defines the contract for applying scheduling rules.
    Implementations can have different rule sets and evaluation strategies.
    """
    
    @abstractmethod
    def calculate_priority_score(
        self,
        current_wait_time: float,
        operator_avg_wait: float,
        progress: float
    ) -> float:
        """
        Calculate weighted priority score based on configured rules.
        
        Args:
            current_wait_time: How long this bus has already waited (minutes)
            operator_avg_wait: Average wait time for this operator's fleet (minutes)
            progress: How far along the bus is in its journey (0-1)
            
        Returns:
            Weighted priority score (higher = higher priority)
        """
        pass  # pragma: no cover
    
    @abstractmethod
    def update_weights(self, weights: Dict[str, float]) -> None:
        """
        Update the weights for the rule engine.
        
        Args:
            weights: Dictionary of rule names to weight values
        """
        pass  # pragma: no cover


class IValidator(ABC):
    """
    Abstract base class for validation strategies.
    
    This interface defines the contract for validating scheduling decisions.
    """
    
    @abstractmethod
    def validate_scenario(self, scenario: Scenario) -> bool:
        """
        Validate that a scenario is well-formed and schedulable.
        
        Args:
            scenario: The scenario to validate
            
        Returns:
            True if valid, False otherwise
            
        Raises:
            ValidationError: If scenario is invalid with specific error message
        """
        pass  # pragma: no cover
    
    @abstractmethod
    def validate_schedule(self, schedule: ScheduleResult) -> bool:
        """
        Validate that a schedule is valid (no constraint violations).
        
        Args:
            schedule: The schedule to validate
            
        Returns:
            True if valid, False otherwise
            
        Raises:
            ValidationError: If schedule is invalid with specific error message
        """
        pass  # pragma: no cover
