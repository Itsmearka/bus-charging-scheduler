"""
Comprehensive unit tests for interfaces.py

This test suite covers all abstract interfaces by creating concrete implementations
to ensure 100% code coverage from a senior developer perspective.
"""

import pytest
from typing import Dict, List
from src.interfaces import ISchedulingStrategy, IPriorityCalculator, IRuleEngine, IValidator
from src.models import Scenario, ScheduleResult, BusSchedule, ChargingEvent, TravelSegment


class ConcreteSchedulingStrategy(ISchedulingStrategy):
    """Concrete implementation of ISchedulingStrategy for testing."""
    
    def schedule(self, scenario: Scenario) -> ScheduleResult:
        """Execute a simple scheduling strategy."""
        # Create a minimal schedule result
        bus_schedules = []
        for bus in scenario.buses:
            schedule = BusSchedule(
                bus_id=bus.bus_id,
                charging_events=[],
                travel_segments=[],
                total_wait_time=0.0,
                final_arrival_time=0.0
            )
            bus_schedules.append(schedule)
        
        from src.models import ScheduleMetrics, StationSchedule
        metrics = ScheduleMetrics(
            total_network_time=0.0,
            avg_wait_per_bus=0.0,
            avg_wait_per_operator={},
            max_wait_time=0.0
        )
        
        station_schedules = []
        for station_id in scenario.stations:
            station_schedule = StationSchedule(
                station_id=station_id,
                charging_queue=[]
            )
            station_schedules.append(station_schedule)
        
        result = ScheduleResult(
            scenario_name=scenario.metadata["name"],
            timestamp="2024-01-01 12:00:00",
            weights_used=scenario.weights,
            bus_schedules=bus_schedules,
            station_schedules=station_schedules,
            metrics=metrics
        )
        return result


class ConcretePriorityCalculator(IPriorityCalculator):
    """Concrete implementation of IPriorityCalculator for testing."""
    
    def calculate_priority(
        self,
        bus_id: str,
        current_wait_time: float,
        operator_avg_wait: float,
        progress: float,
        weights: Dict[str, float]
    ) -> float:
        """Calculate priority score."""
        # Simple calculation: higher wait = higher priority
        return current_wait_time * weights.get("individual", 1.0)


class ConcreteRuleEngine(IRuleEngine):
    """Concrete implementation of IRuleEngine for testing."""
    
    def __init__(self, weights: Dict[str, float]):
        self.weights = weights
    
    def calculate_priority_score(
        self,
        current_wait_time: float,
        operator_avg_wait: float,
        progress: float
    ) -> float:
        """Calculate weighted priority score."""
        individual_score = max(0, 60 - current_wait_time) / 60.0
        operator_score = max(0, 60 - operator_avg_wait) / 60.0
        progress_score = progress
        
        return (
            individual_score * self.weights.get("individual", 1.0) +
            operator_score * self.weights.get("operator", 1.0) +
            progress_score * self.weights.get("overall", 1.0)
        )
    
    def update_weights(self, weights: Dict[str, float]) -> None:
        """Update the weights."""
        self.weights = weights


class ConcreteValidator(IValidator):
    """Concrete implementation of IValidator for testing."""
    
    def validate_scenario(self, scenario: Scenario) -> bool:
        """Validate that a scenario is well-formed."""
        # Check basic structure
        if not scenario.metadata.get("name"):
            return False
        if not scenario.stations:
            return False
        if not scenario.buses:
            return False
        return True
    
    def validate_schedule(self, schedule: ScheduleResult) -> bool:
        """Validate that a schedule is valid."""
        # Check basic structure
        if not schedule.bus_schedules:
            return False
        if not schedule.station_schedules:
            return False
        if schedule.metrics.total_network_time < 0:
            return False
        return True


class TestISchedulingStrategy:
    """Test cases for ISchedulingStrategy interface."""
    
    def test_concrete_scheduling_strategy(self):
        """Test concrete implementation of ISchedulingStrategy."""
        from src.models import WorldConfig, Segment, Route, Station, Bus, Direction
        
        # Create a minimal scenario
        world_config = WorldConfig()
        segments = [Segment("A", "B", 100.0)]
        route = Route("route1", "Test", segments, 100.0)
        stations = {"A": Station("A", "Station A"), "B": Station("B", "Station B")}
        buses = [Bus("bus-001", "kpn", "route1", Direction.FORWARD, "08:00")]
        
        scenario = Scenario(
            metadata={"name": "Test", "description": "Test", "version": "1.0"},
            world_config=world_config,
            routes={"route1": route},
            stations=stations,
            buses=buses,
            weights={"individual": 1.0, "operator": 1.0, "overall": 1.0}
        )
        
        strategy = ConcreteSchedulingStrategy()
        result = strategy.schedule(scenario)
        
        assert result is not None
        assert result.scenario_name == "Test"
        assert len(result.bus_schedules) == 1


class TestIPriorityCalculator:
    """Test cases for IPriorityCalculator interface."""
    
    def test_concrete_priority_calculator(self):
        """Test concrete implementation of IPriorityCalculator."""
        calculator = ConcretePriorityCalculator()
        weights = {"individual": 1.0, "operator": 1.0, "overall": 1.0}
        
        score = calculator.calculate_priority(
            bus_id="bus-001",
            current_wait_time=30.0,
            operator_avg_wait=15.0,
            progress=0.5,
            weights=weights
        )
        
        assert score == 30.0  # current_wait_time * individual_weight


class TestIRuleEngine:
    """Test cases for IRuleEngine interface."""
    
    def test_concrete_rule_engine(self):
        """Test concrete implementation of IRuleEngine."""
        weights = {"individual": 1.0, "operator": 1.0, "overall": 1.0}
        engine = ConcreteRuleEngine(weights)
        
        score = engine.calculate_priority_score(
            current_wait_time=30.0,
            operator_avg_wait=15.0,
            progress=0.5
        )
        
        assert score > 0
    
    def test_concrete_rule_engine_update_weights(self):
        """Test update_weights method."""
        engine = ConcreteRuleEngine({"individual": 1.0, "operator": 1.0, "overall": 1.0})
        new_weights = {"individual": 2.0, "operator": 1.5, "overall": 0.5}
        engine.update_weights(new_weights)
        assert engine.weights == new_weights


class TestIValidator:
    """Test cases for IValidator interface."""
    
    def test_concrete_validator_validate_scenario(self):
        """Test validate_scenario method."""
        from src.models import WorldConfig, Segment, Route, Station, Bus, Direction
        
        # Valid scenario
        world_config = WorldConfig()
        segments = [Segment("A", "B", 100.0)]
        route = Route("route1", "Test", segments, 100.0)
        stations = {"A": Station("A", "Station A"), "B": Station("B", "Station B")}
        buses = [Bus("bus-001", "kpn", "route1", Direction.FORWARD, "08:00")]
        
        scenario = Scenario(
            metadata={"name": "Test", "description": "Test", "version": "1.0"},
            world_config=world_config,
            routes={"route1": route},
            stations=stations,
            buses=buses,
            weights={"individual": 1.0, "operator": 1.0, "overall": 1.0}
        )
        
        validator = ConcreteValidator()
        assert validator.validate_scenario(scenario) == True
        
        # Invalid scenario (missing name)
        scenario.metadata["name"] = ""
        assert validator.validate_scenario(scenario) == False
    
    def test_concrete_validator_validate_schedule(self):
        """Test validate_schedule method."""
        from src.models import ScheduleMetrics, StationSchedule, BusSchedule
        
        # Valid schedule
        bus_schedule = BusSchedule("bus-001", [], [], 0.0, 0.0)
        station_schedule = StationSchedule("A", [])
        metrics = ScheduleMetrics(0.0, 0.0, {}, 0.0)
        
        schedule = ScheduleResult(
            scenario_name="Test",
            timestamp="2024-01-01 12:00:00",
            weights_used={"individual": 1.0, "operator": 1.0, "overall": 1.0},
            bus_schedules=[bus_schedule],
            station_schedules=[station_schedule],
            metrics=metrics
        )
        
        validator = ConcreteValidator()
        assert validator.validate_schedule(schedule) == True
        
        # Invalid schedule (negative network time)
        schedule.metrics.total_network_time = -1.0
        assert validator.validate_schedule(schedule) == False
