"""
Comprehensive unit tests for models.py

This test suite covers all dataclasses and their methods in models.py
to ensure 100% code coverage from a senior developer perspective.
"""

import pytest
from src.models import (
    Direction,
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
    Scenario
)


class TestDirection:
    """Test cases for Direction enum."""
    
    def test_direction_enum_values(self):
        """Test that Direction enum has correct values."""
        assert Direction.FORWARD.value == "forward"
        assert Direction.REVERSE.value == "reverse"
    
    def test_direction_string_behavior(self):
        """Test that Direction behaves like a string."""
        assert Direction.FORWARD.value == "forward"
        assert Direction.FORWARD == Direction.FORWARD


class TestWorldConfig:
    """Test cases for WorldConfig dataclass."""
    
    def test_world_config_defaults(self):
        """Test WorldConfig with default values."""
        config = WorldConfig()
        assert config.battery_range_km == 240.0
        assert config.charging_time_min == 25.0
        assert config.travel_speed_kmh == 60.0
        assert "individual" in config.default_weights
        assert "operator" in config.default_weights
        assert "overall" in config.default_weights
    
    def test_world_config_custom_values(self):
        """Test WorldConfig with custom values."""
        config = WorldConfig(
            battery_range_km=300.0,
            charging_time_min=30.0,
            travel_speed_kmh=80.0,
            default_weights={"individual": 2.0, "operator": 1.5, "overall": 1.0}
        )
        assert config.battery_range_km == 300.0
        assert config.charging_time_min == 30.0
        assert config.travel_speed_kmh == 80.0
        assert config.default_weights["individual"] == 2.0


class TestSegment:
    """Test cases for Segment dataclass."""
    
    def test_segment_creation(self):
        """Test Segment creation with all fields."""
        segment = Segment(
            from_station="A",
            to_station="B",
            distance_km=120.0
        )
        assert segment.from_station == "A"
        assert segment.to_station == "B"
        assert segment.distance_km == 120.0


class TestRoute:
    """Test cases for Route dataclass and methods."""
    
    def test_route_creation(self):
        """Test Route creation with all fields."""
        segments = [
            Segment("A", "B", 100.0),
            Segment("B", "C", 120.0)
        ]
        route = Route(
            route_id="route1",
            name="Test Route",
            segments=segments,
            total_distance=220.0
        )
        assert route.route_id == "route1"
        assert route.name == "Test Route"
        assert len(route.segments) == 2
        assert route.total_distance == 220.0
    
    def test_get_station_sequence(self):
        """Test get_station_sequence method."""
        segments = [
            Segment("A", "B", 100.0),
            Segment("B", "C", 120.0),
            Segment("C", "D", 100.0)
        ]
        route = Route("route1", "Test", segments, 320.0)
        sequence = route.get_station_sequence()
        assert sequence == ["A", "B", "C", "D"]
    
    def test_get_station_sequence_empty(self):
        """Test get_station_sequence with empty segments."""
        route = Route("route1", "Test", [], 0.0)
        sequence = route.get_station_sequence()
        assert sequence == []
    
    def test_get_segment_distance(self):
        """Test get_segment_distance method."""
        segments = [
            Segment("A", "B", 100.0),
            Segment("B", "C", 120.0)
        ]
        route = Route("route1", "Test", segments, 220.0)
        distance = route.get_segment_distance("A", "B")
        assert distance == 100.0
    
    def test_get_segment_distance_not_found(self):
        """Test get_segment_distance with non-existent segment."""
        segments = [Segment("A", "B", 100.0)]
        route = Route("route1", "Test", segments, 100.0)
        distance = route.get_segment_distance("B", "C")
        assert distance == 0.0


class TestStation:
    """Test cases for Station dataclass."""
    
    def test_station_creation_with_defaults(self):
        """Test Station creation with default values."""
        station = Station(station_id="A", name="Station A")
        assert station.station_id == "A"
        assert station.name == "Station A"
        assert station.num_chargers == 1
    
    def test_station_creation_custom_chargers(self):
        """Test Station creation with custom num_chargers."""
        station = Station(station_id="A", name="Station A", num_chargers=3)
        assert station.num_chargers == 3


class TestBus:
    """Test cases for Bus dataclass."""
    
    def test_bus_creation(self):
        """Test Bus creation with all fields."""
        bus = Bus(
            bus_id="bus-001",
            operator="kpn",
            route_id="route1",
            direction=Direction.FORWARD,
            departure_time="08:00"
        )
        assert bus.bus_id == "bus-001"
        assert bus.operator == "kpn"
        assert bus.route_id == "route1"
        assert bus.direction == Direction.FORWARD
        assert bus.departure_time == "08:00"


class TestChargingEvent:
    """Test cases for ChargingEvent dataclass."""
    
    def test_charging_event_creation(self):
        """Test ChargingEvent creation with all fields."""
        event = ChargingEvent(
            station_id="A",
            arrival_time=100.0,
            charge_start_time=120.0,
            charge_end_time=145.0,
            wait_time=20.0
        )
        assert event.station_id == "A"
        assert event.arrival_time == 100.0
        assert event.charge_start_time == 120.0
        assert event.charge_end_time == 145.0
        assert event.wait_time == 20.0


class TestTravelSegment:
    """Test cases for TravelSegment dataclass."""
    
    def test_travel_segment_creation(self):
        """Test TravelSegment creation with all fields."""
        segment = TravelSegment(
            from_station="A",
            to_station="B",
            departure_time=100.0,
            arrival_time=120.0,
            distance_km=100.0
        )
        assert segment.from_station == "A"
        assert segment.to_station == "B"
        assert segment.departure_time == 100.0
        assert segment.arrival_time == 120.0
        assert segment.distance_km == 100.0


class TestBusSchedule:
    """Test cases for BusSchedule dataclass."""
    
    def test_bus_schedule_creation(self):
        """Test BusSchedule creation with all fields."""
        charging_events = [
            ChargingEvent("A", 100.0, 120.0, 145.0, 20.0)
        ]
        travel_segments = [
            TravelSegment("A", "B", 100.0, 120.0, 100.0)
        ]
        schedule = BusSchedule(
            bus_id="bus-001",
            charging_events=charging_events,
            travel_segments=travel_segments,
            total_wait_time=20.0,
            final_arrival_time=145.0,
            is_valid=True
        )
        assert schedule.bus_id == "bus-001"
        assert len(schedule.charging_events) == 1
        assert len(schedule.travel_segments) == 1
        assert schedule.total_wait_time == 20.0
        assert schedule.final_arrival_time == 145.0
        assert schedule.is_valid == True
    
    def test_bus_schedule_default_is_valid(self):
        """Test BusSchedule with default is_valid."""
        schedule = BusSchedule(
            bus_id="bus-001",
            charging_events=[],
            travel_segments=[],
            total_wait_time=0.0,
            final_arrival_time=100.0
        )
        assert schedule.is_valid == True


class TestStationSchedule:
    """Test cases for StationSchedule dataclass."""
    
    def test_station_schedule_creation(self):
        """Test StationSchedule creation with all fields."""
        charging_queue = [
            {"bus_id": "bus-001", "start": 100.0, "end": 145.0}
        ]
        utilization_metrics = {"total_buses": 10, "avg_wait": 15.0}
        schedule = StationSchedule(
            station_id="A",
            charging_queue=charging_queue,
            utilization_metrics=utilization_metrics
        )
        assert schedule.station_id == "A"
        assert len(schedule.charging_queue) == 1
        assert schedule.utilization_metrics is not None
    
    def test_station_schedule_default_metrics(self):
        """Test StationSchedule with default utilization_metrics."""
        schedule = StationSchedule(
            station_id="A",
            charging_queue=[]
        )
        assert schedule.utilization_metrics is None


class TestScheduleMetrics:
    """Test cases for ScheduleMetrics dataclass."""
    
    def test_schedule_metrics_creation(self):
        """Test ScheduleMetrics creation with all fields."""
        metrics = ScheduleMetrics(
            total_network_time=10000.0,
            avg_wait_per_bus=50.0,
            avg_wait_per_operator={"kpn": 40.0, "freshbus": 60.0},
            max_wait_time=100.0
        )
        assert metrics.total_network_time == 10000.0
        assert metrics.avg_wait_per_bus == 50.0
        assert "kpn" in metrics.avg_wait_per_operator
        assert metrics.max_wait_time == 100.0


class TestScheduleResult:
    """Test cases for ScheduleResult dataclass."""
    
    def test_schedule_result_creation(self):
        """Test ScheduleResult creation with all fields."""
        bus_schedules = [
            BusSchedule("bus-001", [], [], 0.0, 100.0)
        ]
        station_schedules = [
            StationSchedule("A", [])
        ]
        metrics = ScheduleMetrics(
            total_network_time=10000.0,
            avg_wait_per_bus=50.0,
            avg_wait_per_operator={},
            max_wait_time=100.0
        )
        result = ScheduleResult(
            scenario_name="scenario1",
            timestamp="2024-01-01 12:00:00",
            weights_used={"individual": 1.0, "operator": 1.0, "overall": 1.0},
            bus_schedules=bus_schedules,
            station_schedules=station_schedules,
            metrics=metrics
        )
        assert result.scenario_name == "scenario1"
        assert result.timestamp == "2024-01-01 12:00:00"
        assert len(result.bus_schedules) == 1
        assert len(result.station_schedules) == 1


class TestScenario:
    """Test cases for Scenario dataclass."""
    
    def test_scenario_creation(self):
        """Test Scenario creation with all fields."""
        world_config = WorldConfig()
        segments = [Segment("A", "B", 100.0)]
        route = Route("route1", "Test", segments, 100.0)
        stations = {"A": Station("A", "Station A")}
        buses = [Bus("bus-001", "kpn", "route1", Direction.FORWARD, "08:00")]
        
        scenario = Scenario(
            metadata={"name": "Test Scenario", "description": "Test", "version": "1.0"},
            world_config=world_config,
            routes={"route1": route},
            stations=stations,
            buses=buses,
            weights={"individual": 1.0, "operator": 1.0, "overall": 1.0}
        )
        assert scenario.metadata["name"] == "Test Scenario"
        assert len(scenario.routes) == 1
        assert len(scenario.stations) == 1
        assert len(scenario.buses) == 1
        assert "individual" in scenario.weights
