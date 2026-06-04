"""
Data models for Bus Charging Scheduler.
Uses Pydantic for validation and type safety.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field, validator


class Station(BaseModel):
    """Represents a charging station along the route."""
    
    id: str = Field(..., description="Station identifier (e.g., 'A', 'B')")
    name: str = Field(..., description="Human-readable station name")
    chargers_count: int = Field(1, ge=1, description="Number of chargers at this station")
    location_km: int = Field(..., ge=0, description="Distance from Bengaluru in km")
    
    class Config:
        frozen = True  # Immutable


class RouteSegment(BaseModel):
    """Represents a segment of the route between two locations."""
    
    from_location: str = Field(..., description="Starting location")
    to_location: str = Field(..., description="Ending location")
    distance_km: int = Field(..., gt=0, description="Segment distance in km")
    
    class Config:
        frozen = True


class Route(BaseModel):
    """Represents the complete route with all segments and stations."""
    
    segments: List[RouteSegment] = Field(..., description="List of route segments")
    stations: List[Station] = Field(..., description="List of charging stations")
    total_distance_km: int = Field(..., gt=0, description="Total route distance")
    
    @validator('total_distance_km')
    def validate_total_distance(cls, v, values):
        """Ensure total distance matches sum of segments."""
        if 'segments' in values:
            calculated = sum(seg.distance_km for seg in values['segments'])
            if v != calculated:
                raise ValueError(f"Total distance {v} doesn't match sum of segments {calculated}")
        return v


class Bus(BaseModel):
    """Represents a bus with its schedule and operator."""
    
    id: str = Field(..., description="Unique bus identifier (e.g., 'bus-BK-01')")
    operator: str = Field(..., description="Operator name (kpn, freshbus, flixbus)")
    direction: str = Field(..., description="Direction: 'BK' (Bengaluru→Kochi) or 'KB' (Kochi→Bengaluru)")
    departure_time_minutes: int = Field(..., ge=0, description="Departure time in minutes from midnight")
    
    # Future extension fields (not used yet, but ready for future)
    priority: Optional[int] = Field(None, description="Priority level (for future use)")
    route_id: Optional[str] = Field(None, description="Route identifier (for multi-route scenarios)")
    
    @validator('direction')
    def validate_direction(cls, v):
        """Ensure direction is valid."""
        if v not in ['BK', 'KB']:
            raise ValueError(f"Direction must be 'BK' or 'KB', got '{v}'")
        return v
    
    @validator('operator')
    def validate_operator(cls, v):
        """Ensure operator is valid."""
        valid_operators = ['kpn', 'freshbus', 'flixbus']
        if v.lower() not in valid_operators:
            raise ValueError(f"Operator must be one of {valid_operators}, got '{v}'")
        return v.lower()


class ChargingEvent(BaseModel):
    """Represents a single charging event at a station."""
    
    bus_id: str = Field(..., description="Bus identifier")
    station_id: str = Field(..., description="Station identifier")
    arrival_time_minutes: int = Field(..., ge=0, description="When bus arrives at station")
    start_time_minutes: int = Field(..., ge=0, description="When charging starts")
    end_time_minutes: int = Field(..., ge=0, description="When charging ends")
    wait_time_minutes: int = Field(..., ge=0, description="Wait time in queue")
    
    # Future extension fields
    cost_multiplier: Optional[float] = Field(None, description="Time-of-day pricing multiplier")
    
    @validator('wait_time_minutes')
    def validate_wait_time(cls, v, values):
        """Ensure wait time is consistent with arrival and start times."""
        if 'arrival_time_minutes' in values and 'start_time_minutes' in values:
            calculated_wait = values['start_time_minutes'] - values['arrival_time_minutes']
            if v != calculated_wait:
                raise ValueError(f"Wait time {v} doesn't match start - arrival = {calculated_wait}")
        return v
    
    @validator('end_time_minutes')
    def validate_end_time(cls, v, values):
        """Ensure end time is after start time."""
        if 'start_time_minutes' in values:
            if v <= values['start_time_minutes']:
                raise ValueError(f"End time {v} must be after start time {values['start_time_minutes']}")
        return v


class ChargingPlan(BaseModel):
    """Represents the complete charging plan for a single bus."""
    
    bus_id: str = Field(..., description="Bus identifier")
    events: List[ChargingEvent] = Field(default_factory=list, description="List of charging events")
    total_wait_time_minutes: int = Field(..., ge=0, description="Total wait time across all events")
    arrival_time_minutes: int = Field(..., ge=0, description="Final arrival time at destination")
    departure_time_minutes: int = Field(..., ge=0, description="Departure time from origin")
    
    @validator('total_wait_time_minutes')
    def validate_total_wait(cls, v, values):
        """Ensure total wait time matches sum of event wait times."""
        if 'events' in values:
            calculated = sum(event.wait_time_minutes for event in values['events'])
            if v != calculated:
                raise ValueError(f"Total wait {v} doesn't match sum of events {calculated}")
        return v


class Scenario(BaseModel):
    """Represents a complete scenario with buses, route, and configuration."""
    
    name: str = Field(..., description="Scenario name")
    description: str = Field("", description="Scenario description")
    buses: List[Bus] = Field(..., description="List of buses in this scenario")
    weights: Dict[str, float] = Field(..., description="Optimization weights")
    
    # Overrides for global config (optional)
    battery_range_km: Optional[int] = Field(None, description="Override for battery range")
    charging_time_minutes: Optional[int] = Field(None, description="Override for charging time")
    bus_speed_kmh: Optional[int] = Field(None, description="Override for bus speed")
    
    @validator('weights')
    def validate_weights(cls, v):
        """Ensure all required weights are present."""
        required = ['individual', 'operator', 'overall']
        for key in required:
            if key not in v:
                raise ValueError(f"Missing required weight: {key}")
            if v[key] < 0:
                raise ValueError(f"Weight {key} must be non-negative, got {v[key]}")
        return v
    
    @validator('buses')
    def validate_buses(cls, v):
        """Ensure bus IDs are unique."""
        ids = [bus.id for bus in v]
        if len(ids) != len(set(ids)):
            raise ValueError("Bus IDs must be unique")
        return v


class SchedulerResult(BaseModel):
    """Represents the output of the scheduler."""
    
    scenario_name: str = Field(..., description="Scenario name")
    plans: List[ChargingPlan] = Field(..., description="Charging plans for all buses")
    solve_time_seconds: float = Field(..., ge=0, description="Time taken to solve")
    optimization_enabled: bool = Field(..., description="Whether Phase 2 optimizations were used")
    solver_status: str = Field(..., description="Solver status (OPTIMAL, FEASIBLE, INFEASIBLE)")
    
    # Metrics
    total_wait_time_minutes: int = Field(..., ge=0, description="Total wait across all buses")
    max_wait_time_minutes: int = Field(..., ge=0, description="Maximum wait for any single bus")
    average_wait_time_minutes: float = Field(..., ge=0, description="Average wait per bus")
    
    # Solver statistics
    num_variables: int = Field(default=0, ge=0, description="Number of decision variables in model")
    num_constraints: int = Field(default=0, ge=0, description="Number of constraints in model")
    branches_explored: int = Field(default=0, ge=0, description="Number of branches explored by solver")
    conflicts: int = Field(default=0, ge=0, description="Number of conflicts resolved by solver")
    objective_value: Optional[int] = Field(default=None, description="Objective value of solution")
    objective_bound: Optional[int] = Field(default=None, description="Best known objective bound")
    optimality_gap_percent: Optional[float] = Field(default=None, ge=0, description="Optimality gap percentage")
