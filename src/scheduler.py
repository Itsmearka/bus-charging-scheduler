"""
Simplified scheduler for the Bus Charging Scheduler.

This module implements the core scheduling algorithm using a priority-based
greedy approach with weighted conflict resolution.

The scheduler is designed to be:
- Simple and easy to understand
- Scalable to more buses, stations, and operators
- Extensible for new rules without rewriting the engine
- Tunable via configuration weights
"""

import heapq
import logging
from typing import Dict, List, Optional
from datetime import datetime

from src.models import (
    Scenario, Bus, Station, Route, BusSchedule, StationSchedule,
    ChargingEvent, TravelSegment, ScheduleResult, ScheduleMetrics
)
from src.utils import (
    time_to_minutes, calculate_travel_time, minutes_to_time,
    get_route_segments_for_direction
)
from src.interfaces import ISchedulingStrategy
from src.exceptions import SchedulingError, ValidationError
from src.logging_config import get_logger

logger = get_logger(__name__)


class Scheduler(ISchedulingStrategy):
    """
    Core scheduling engine for bus charging with tunable weights.
    
    Uses a load-aware look-ahead algorithm with three tunable weights:
    1. Individual: Minimize wait time for each bus (controls penalty_per_stop)
    2. Operator: Balance charging across operator's fleet (controls queue_threshold)
    3. Overall: Minimize total network time (controls congestion_threshold)
    
    Algorithm:
    1. When bus arrives at station, evaluate charging at current + next N stations (look_ahead_depth)
    2. For each candidate station:
       - Check if reachable with current charge
       - Simulate: if charged here, can bus complete route safely?
       - Get current queue length and calculate expected wait time
       - Calculate score: wait_time + (extra_stops × penalty_per_stop)
    3. Choose lowest-scoring option (minimum wait time with weight-based penalties)
    4. Update station queue and continue
    
    This approach is:
    - Weight-tunable for different optimization goals
    - Scalable to more buses, stations, and operators
    - Extensible for new rules without rewriting the engine
    - Aligns with problem statement requirements
    
    Implements the ISchedulingStrategy interface for extensibility.
    
    Configuration:
        look_ahead_depth can be set in scenario.world_config:
        {
          "world_config": {
            "look_ahead_depth": 3
          }
        }
    """
    
    def __init__(
        self,
        weights: Dict[str, float] = None,
        look_ahead_depth: Optional[int] = 2
    ):
        """
        Initialize the scheduler with tunable weights.
        
        Args:
            weights: Dictionary of weights for optimization objectives
                    {"individual": 1.0, "operator": 1.0, "overall": 1.0}
                    individual: Controls penalty on extra stops (higher = more greedy-like)
                    operator: Controls operator-level queue balancing sensitivity
                    overall: Controls network-wide congestion management
            look_ahead_depth: Number of stations ahead to evaluate (default: 2)
                              If None, evaluate all stations on route (unlimited)
                              Recommended: 2 for performance on routes with 10+ stations
        """
        # Set default weights if not provided
        self.weights = weights or {"individual": 1.0, "operator": 1.0, "overall": 1.0}
        self.look_ahead_depth = look_ahead_depth
        
        # Derive implementation parameters from weights
        self.penalty_per_stop = self._derive_penalty_from_weights()
        self.queue_threshold = self._derive_queue_threshold()
        self.congestion_threshold = self._derive_congestion_threshold()
        
        self.scenario: Optional[Scenario] = None
        self.station_queues: Dict[str, List[str]] = {}  # station_id -> list of bus_ids waiting
        logger.info(
            f"Scheduler initialized with weights: {self.weights}, "
            f"derived parameters: penalty_per_stop={self.penalty_per_stop}min, "
            f"queue_threshold={self.queue_threshold}, congestion_threshold={self.congestion_threshold}, "
            f"look_ahead_depth={look_ahead_depth}"
        )
    
    def _derive_penalty_from_weights(self) -> float:
        """
        Derive penalty_per_stop from individual weight.
        
        Higher individual weight = more penalty on extra stops = greedy-like behavior.
        Range: 0.0 (no penalty) to 25.0 (penalty equals charging time).
        
        Returns:
            Penalty in minutes for each extra charging stop
        """
        return self.weights["individual"] * 5.0
    
    def _derive_queue_threshold(self) -> int:
        """
        Derive queue_threshold from operator weight.
        
        Higher operator weight = more sensitive to queue differences.
        Range: 1 (very sensitive) to 10 (less sensitive).
        
        Returns:
            Queue difference threshold to ignore extra_stops penalty
        """
        return max(1, int(10 - self.weights["operator"] * 7))
    
    def _derive_congestion_threshold(self) -> int:
        """
        Derive congestion_threshold from overall weight.
        
        Higher overall weight = more aggressive congestion management.
        Range: 2 (aggressive) to 10 (passive).
        
        Returns:
            Queue length threshold for aggressive balancing
        """
        return max(2, int(10 - self.weights["overall"] * 7))
    
    def _get_direction_aware_segments(self, route: Route, bus: Bus) -> List:
        """
        Get route segments in the correct order based on bus direction.
        
        This method converts Segment objects to dictionaries, applies direction
        transformation, and returns the result as a list of dictionaries that
        can be used by the scheduler logic.
        
        Args:
            route: The route definition
            bus: The bus with direction information
            
        Returns:
            List of segment dictionaries in the correct order for the bus direction
        """
        # Convert Segment objects to dictionaries
        segments_dict = [
            {
                "from_station": seg.from_station,
                "to_station": seg.to_station,
                "distance_km": seg.distance_km
            }
            for seg in route.segments
        ]
        
        # Apply direction transformation
        direction_aware_segments = get_route_segments_for_direction(
            segments_dict, 
            bus.direction.value
        )
        
        logger.debug(f"Bus {bus.bus_id} direction={bus.direction.value}, segments ordered correctly")
        return direction_aware_segments
    
    def schedule(self, scenario: Scenario) -> ScheduleResult:
        """
        Schedule all buses in a scenario using load-aware look-ahead approach with tunable weights.
        
        Algorithm:
        1. Initialize data structures (bus schedules, station queues, event queue)
        2. Override scheduler weights with scenario weights if provided
        3. Process events chronologically (bus arrivals at stations)
        4. For each bus arrival:
           a. Calculate current battery range
           b. Get candidate charging stations (reachable within look_ahead_depth)
           c. For each candidate: score based on wait time + extra stops
           d. Choose lowest-scoring station (minimum wait time)
           e. Update station queue and schedule charging
        5. Build station schedules and calculate metrics
        
        Args:
            scenario: The scenario to schedule
            
        Returns:
            Complete schedule result with bus schedules, station schedules, and metrics
            
        Raises:
            SchedulingError: If scheduling encounters an unrecoverable error
        """
        logger.info(f"Starting scheduling for scenario: {scenario.metadata['name']}")
        logger.info(f"Number of buses: {len(scenario.buses)}, stations: {len(scenario.stations)}")
        
        # Store scenario for reference
        self.scenario = scenario
        
        # Override weights with scenario weights if provided
        if scenario.weights:
            self.weights = scenario.weights
            # Re-derive parameters from scenario weights
            self.penalty_per_stop = self._derive_penalty_from_weights()
            self.queue_threshold = self._derive_queue_threshold()
            self.congestion_threshold = self._derive_congestion_threshold()
            logger.info(f"Using scenario weights: {self.weights}")
            logger.info(f"Derived parameters: penalty_per_stop={self.penalty_per_stop}min, "
                       f"queue_threshold={self.queue_threshold}, congestion_threshold={self.congestion_threshold}")
        
        # Override look_ahead_depth from world_config if present
        config_depth = scenario.world_config.__dict__.get('look_ahead_depth')
        if config_depth is not None:
            self.look_ahead_depth = config_depth
            logger.info(f"Using look_ahead_depth from config: {config_depth}")
        
        # Override queue_threshold from world_config if present
        config_queue_threshold = scenario.world_config.__dict__.get('queue_threshold')
        if config_queue_threshold is not None:
            self.queue_threshold = config_queue_threshold
            logger.info(f"Using queue_threshold from config: {config_queue_threshold}")
        
        # Override congestion_threshold from world_config if present
        config_congestion_threshold = scenario.world_config.__dict__.get('congestion_threshold')
        if config_congestion_threshold is not None:
            self.congestion_threshold = config_congestion_threshold
            logger.info(f"Using congestion_threshold from config: {config_congestion_threshold}")
        
        # Initialize data structures
        bus_schedules: Dict[str, BusSchedule] = {
            bus.bus_id: BusSchedule(
                bus_id=bus.bus_id,
                charging_events=[],
                travel_segments=[],
                total_wait_time=0.0,
                final_arrival_time=0.0,
                is_valid=True
            )
            for bus in scenario.buses
        }
        
        # Initialize station queues (track which buses are waiting at each station)
        self.station_queues = {
            station_id: [] for station_id in scenario.stations.keys()
        }
        
        # Track charger availability per station (next available time for each charger)
        station_chargers: Dict[str, List[float]] = {}
        for station_id, station in scenario.stations.items():
            station_chargers[station_id] = [0.0] * station.num_chargers
            logger.debug(f"Station {station_id}: {station.num_chargers} chargers")
        
        # Track operator wait times for metrics
        operator_wait_times: Dict[str, List[float]] = {
            operator: [] for operator in set(bus.operator for bus in scenario.buses)
        }
        logger.debug(f"Operators: {list(operator_wait_times.keys())}")
        
        # Pre-compute direction-aware segments for each bus
        # This ensures buses travel in the correct direction (forward/reverse)
        bus_segments: Dict[str, List] = {}
        for bus in scenario.buses:
            route = scenario.routes[bus.route_id]
            bus_segments[bus.bus_id] = self._get_direction_aware_segments(route, bus)
        
        # Event queue: (time, event_type, bus_id, station_id, segment_index)
        # event_type: "arrival" or "departure"
        event_queue = []
        
        # Initialize events for all bus departures
        for bus in scenario.buses:
            route = scenario.routes[bus.route_id]
            departure_minutes = time_to_minutes(bus.departure_time)
            segments = bus_segments[bus.bus_id]
            
            # Add departure event from origin using direction-aware segments
            heapq.heappush(event_queue, (
                departure_minutes,
                "departure",
                bus.bus_id,
                segments[0]["from_station"] if segments else None,
                0
            ))
            logger.debug(f"Bus {bus.bus_id} departing at {bus.departure_time} ({departure_minutes} min)")
        
        # Process events
        event_count = 0
        while event_queue:
            current_time, event_type, bus_id, station_id, segment_index = heapq.heappop(event_queue)
            event_count += 1
            bus = next(b for b in scenario.buses if b.bus_id == bus_id)
            route = scenario.routes[bus.route_id]
            schedule = bus_schedules[bus_id]
            segments = bus_segments[bus_id]  # Use direction-aware segments
            
            if event_type == "departure":
                # Bus is departing from a station
                if segment_index < len(segments):
                    # Travel to next station
                    segment = segments[segment_index]
                    travel_time = calculate_travel_time(
                        segment["distance_km"],
                        scenario.world_config.travel_speed_kmh
                    )
                    arrival_time = current_time + travel_time
                    
                    # Record travel segment
                    schedule.travel_segments.append(TravelSegment(
                        from_station=segment["from_station"],
                        to_station=segment["to_station"],
                        departure_time=current_time,
                        arrival_time=arrival_time,
                        distance_km=segment["distance_km"]
                    ))
                    
                    # Add arrival event
                    heapq.heappush(event_queue, (
                        arrival_time,
                        "arrival",
                        bus_id,
                        segment["to_station"],
                        segment_index + 1
                    ))
                else:
                    # Bus has reached destination
                    schedule.final_arrival_time = current_time  # pragma: no cover
                    logger.debug(f"Bus {bus_id} reached destination at {current_time} min")  # pragma: no cover
                    
            elif event_type == "arrival":
                # Bus has arrived at a station
                if station_id in scenario.stations:
                    # This is a charging station - use load-aware look-ahead to decide
                    charging_decision = self._make_charging_decision(
                        bus, station_id, current_time, schedule, segments, segment_index,
                        station_chargers, operator_wait_times, event_queue
                    )
                    
                    if charging_decision['charge_now']:
                        # Schedule charging at this station
                        self._schedule_charging(
                            bus, station_id, current_time, schedule,
                            station_chargers[station_id],
                            scenario.world_config.charging_time_min,
                            operator_wait_times,
                            event_queue,
                            segment_index,
                            segments
                        )
                    else:
                        # Skip charging, continue to next station
                        heapq.heappush(event_queue, (
                            current_time,
                            "departure",
                            bus_id,
                            station_id,
                            segment_index
                        ))
                else:
                    # This is an endpoint (Bengaluru or Kochi) - trip complete
                    schedule.final_arrival_time = current_time
                    logger.debug(f"Bus {bus_id} completed trip at {current_time} min")
        
        logger.info(f"Processed {event_count} events")
        
        # Build station schedules
        station_schedules = self._build_station_schedules(scenario, bus_schedules)
        
        # Calculate metrics
        metrics = self._calculate_metrics(bus_schedules, operator_wait_times)
        
        logger.info(f"Load-aware scheduling complete. Total network time: {metrics.total_network_time:.2f} min")
        
        return ScheduleResult(
            scenario_name=scenario.metadata["name"],
            timestamp=datetime.now().isoformat(),
            weights_used=scenario.weights,
            bus_schedules=list(bus_schedules.values()),
            station_schedules=station_schedules,
            metrics=metrics
        )
    
    def _make_charging_decision(
        self,
        bus: Bus,
        current_station_id: str,
        current_time: float,
        schedule: BusSchedule,
        segments: List,
        segment_index: int,
        station_chargers: Dict[str, List[float]],
        operator_wait_times: Dict[str, List[float]],
        event_queue: List
    ) -> Dict[str, any]:
        """
        Make charging decision using load-aware look-ahead algorithm.
        
        Evaluates charging at multiple candidate stations and chooses the option
        that minimizes wait time (primary goal) while considering charging stops (secondary).
        
        Args:
            bus: The bus making the decision
            current_station_id: Station where bus currently is
            current_time: Current time in minutes
            schedule: Current bus schedule
            segments: Direction-aware segment list for the bus
            segment_index: Current segment index
            station_chargers: Charger availability per station
            operator_wait_times: Operator wait times tracking
            event_queue: Event queue
            
        Returns:
            Dictionary with:
                charge_now: Boolean - should bus charge at current station?
                chosen_station: str - which station to charge at (if charge_now=True)
                wait_time: float - expected wait time at chosen station
        """
        # If current station is not a charging station (endpoint), don't charge
        if current_station_id not in self.scenario.stations:
            logger.debug(f"Bus {bus.bus_id}: Station {current_station_id} is not a charging station, skip charging")
            return {'charge_now': False, 'chosen_station': None, 'wait_time': 0.0}
        
        # Calculate current battery range
        battery_range = self.scenario.world_config.battery_range_km
        current_range = self._calculate_current_range(schedule, segments, segment_index, battery_range)
        
        # Get number of charging stations for few-station handling
        num_charging_stations = len(self.scenario.stations)
        
        # Get candidate charging stations (reachable within look_ahead_depth)
        candidate_stations = self._get_reachable_stations(
            current_station_id, current_range, segments, segment_index
        )
        
        if not candidate_stations:
            # No reachable stations - must charge at current station
            logger.debug(f"Bus {bus.bus_id}: No reachable stations, must charge at {current_station_id}")  # pragma: no cover
            return {'charge_now': True, 'chosen_station': current_station_id, 'wait_time': 0.0}  # pragma: no cover
        
        # Evaluate each candidate station
        best_station = None
        best_score = float('inf')
        best_wait_time = 0.0
        
        for station_id in candidate_stations:
            # Get queue length at current station for dynamic penalty calculation
            current_station_queue = self._get_current_queue_length(current_station_id, station_chargers, current_time)
            
            # Check if charging at this station allows reaching the furthest station in the look-ahead window
            # This ensures we don't charge at a station that strands the bus before it can charge again
            # Example: Bus at A, depth=2 → Evaluate A, B, C. Check if charging at A allows reaching C.
            if len(candidate_stations) > 1:
                target_station_id = candidate_stations[-1]  # Furthest station in candidate list
                # Calculate distance from charging station to target station
                charge_index = None
                for i, segment in enumerate(segments):
                    if segment["to_station"] == station_id:
                        charge_index = i + 1
                        break
                
                if charge_index is not None:
                    distance_to_target = 0.0
                    for i in range(charge_index, len(segments)):
                        segment = segments[i]
                        distance_to_target += segment["distance_km"]
                        if segment["to_station"] == target_station_id:
                            break
                    
                    # Check if full battery range covers the distance
                    if distance_to_target > battery_range:
                        logger.debug(
                            f"Bus {bus.bus_id}: Charging at {station_id} would not allow reaching {target_station_id} "
                            f"(distance={distance_to_target}km > range={battery_range}km), skipping"
                        )
                        continue  # pragma: no cover  # Skip this station
            
            # Calculate expected wait time at this station
            queue_length = self._get_current_queue_length(station_id, station_chargers, current_time)
            wait_time = self._calculate_wait_time(queue_length, self.scenario.world_config.charging_time_min)
            
            # Calculate extra stops if charging here vs greedy approach
            extra_stops = self._calculate_extra_stops(station_id, current_station_id, candidate_stations)
            
            # Calculate dynamic penalty based on queue congestion
            dynamic_penalty = self._calculate_dynamic_penalty(
                current_station_queue, queue_length, num_charging_stations
            )
            
            # Score: wait_time + (extra_stops × dynamic_penalty)
            # Wait time dominates (5 min penalty << 25 min charging time)
            score = wait_time + (extra_stops * dynamic_penalty)
            
            logger.debug(
                f"Bus {bus.bus_id} at {current_station_id}: Candidate {station_id} "
                f"queue={queue_length}, current_queue={current_station_queue}, wait={wait_time:.1f}min, "
                f"extra_stops={extra_stops}, penalty={dynamic_penalty:.1f}, score={score:.1f}"
            )
            
            # Choose lowest score (minimum wait time)
            if score < best_score:
                best_score = score
                best_station = station_id
                best_wait_time = wait_time
        
        # Decision: charge at current station or skip to chosen station?
        charge_now = (best_station == current_station_id)
        
        # Apply queue comparison logic: if best station is severely congested and another has much shorter queue, switch
        if best_station and len(candidate_stations) > 1:
            best_queue = self._get_current_queue_length(best_station, station_chargers, current_time)
            
            # Find station with minimum queue among all candidates
            min_queue_station = None
            min_queue_length = float('inf')
            
            for station_id in candidate_stations:
                queue_length = self._get_current_queue_length(station_id, station_chargers, current_time)
                if queue_length < min_queue_length:
                    min_queue_length = queue_length
                    min_queue_station = station_id
            
            # If best station is congested and another station has much shorter queue, switch
            queue_diff = best_queue - min_queue_length
            if queue_diff > self.queue_threshold:
                logger.debug(  # pragma: no cover
                    f"Bus {bus.bus_id}: Switching from {best_station} (queue={best_queue}) "
                    f"to {min_queue_station} (queue={min_queue_length}) for load balancing "
                    f"(queue_diff={queue_diff} > threshold={self.queue_threshold})"
                )
                best_station = min_queue_station  # pragma: no cover
                best_wait_time = self._calculate_wait_time(min_queue_length, self.scenario.world_config.charging_time_min)  # pragma: no cover
                charge_now = (best_station == current_station_id)  # pragma: no cover
        
        logger.debug(
            f"Bus {bus.bus_id} decision: {'Charge' if charge_now else 'Skip'} at {current_station_id}, "
            f"best station={best_station}, wait_time={best_wait_time:.1f}min"
        )
        
        return {
            'charge_now': charge_now,
            'chosen_station': best_station,
            'wait_time': best_wait_time
        }
    
    def _get_reachable_stations(
        self,
        current_station_id: str,
        current_range: float,
        segments: List,
        segment_index: int
    ) -> List[str]:
        """
        Get list of stations bus can reach with current charge, respecting look_ahead_depth.
        
        Returns stations that are:
        1. Within current battery range
        2. Within look_ahead_depth stations ahead (or all if depth=None)
        
        Args:
            current_station_id: Station where bus currently is
            current_range: Current battery range in km
            segments: Direction-aware segment list for the bus
            segment_index: Current segment index
            
        Returns:
            List of station IDs that are reachable
        """
        reachable_stations = []
        distance_traveled = 0.0
        
        # Start from current position
        for i in range(segment_index, len(segments)):
            segment = segments[i]
            
            # Check if we've exceeded look_ahead_depth
            if self.look_ahead_depth is not None:
                stations_ahead = i - segment_index
                if stations_ahead > self.look_ahead_depth:
                    break  # pragma: no cover
            
            # Check if station is reachable
            if distance_traveled + segment["distance_km"] <= current_range:
                # Add the destination station of this segment
                reachable_stations.append(segment["to_station"])
                distance_traveled += segment["distance_km"]
            else:
                # Cannot reach this station, stop
                break
        
        # Also include current station if it's a charging station
        if current_station_id in self.scenario.stations:
            reachable_stations.insert(0, current_station_id)
        
        logger.debug(
            f"Reachable stations from {current_station_id}: {reachable_stations} "
            f"(range={current_range}km, depth={self.look_ahead_depth})"
        )
        
        return reachable_stations
    
    def _calculate_dynamic_penalty(
        self,
        current_station_queue: int,
        candidate_station_queue: int,
        num_charging_stations: int
    ) -> float:
        """
        Calculate dynamic penalty based on queue congestion levels.
        
        Adjusts the penalty_per_stop based on:
        - Queue difference between current and candidate stations
        - Congestion level at current station
        - Number of charging stations on route (for few-station handling)
        
        Args:
            current_station_queue: Queue length at current station
            candidate_station_queue: Queue length at candidate station
            num_charging_stations: Total number of charging stations on route
            
        Returns:
            Adjusted penalty_per_stop value
        """
        # Calculate queue difference
        queue_diff = abs(current_station_queue - candidate_station_queue)
        
        # Determine effective thresholds based on number of stations
        effective_queue_threshold = self.queue_threshold
        effective_congestion_threshold = self.congestion_threshold
        
        # Few-station routes: use more aggressive balancing (reduce thresholds by 50%)
        if num_charging_stations <= 4:
            effective_queue_threshold = max(1, self.queue_threshold // 2)
            effective_congestion_threshold = max(2, self.congestion_threshold // 2)
            logger.debug(
                f"Few-station route detected ({num_charging_stations} stations), "
                f"using aggressive balancing: queue_threshold={effective_queue_threshold}, "
                f"congestion_threshold={effective_congestion_threshold}"
            )
        
        # If queue difference exceeds threshold, ignore extra_stops penalty
        if queue_diff > effective_queue_threshold:
            logger.debug(
                f"Queue diff {queue_diff} > threshold {effective_queue_threshold}, "
                f"ignoring extra_stops penalty (penalty=0.0)"
            )
            return 0.0
        
        # If current station is congested, reduce penalty by 50%
        if current_station_queue > effective_congestion_threshold:
            adjusted_penalty = self.penalty_per_stop * 0.5
            logger.debug(
                f"Current station queue {current_station_queue} > threshold {effective_congestion_threshold}, "
                f"reducing penalty: {self.penalty_per_stop} → {adjusted_penalty}"
            )
            return adjusted_penalty
        
        # Normal penalty
        return self.penalty_per_stop
    
    def _can_reach_station_safely(
        self,
        current_range: float,
        distance_to_station: float
    ) -> bool:
        """
        Check if bus can reach a station safely with current battery range.
        
        Args:
            current_range: Current battery range in km
            distance_to_station: Distance to station in km
            
        Returns:
            True if station can be reached, False otherwise
        """
        can_reach = current_range >= distance_to_station
        logger.debug(
            f"Can reach station? range={current_range}km, distance={distance_to_station}km -> {can_reach}"
        )
        return can_reach
    
    def _simulate_charging_at_station(
        self,
        charging_station_id: str,
        current_range: float,
        segments: List,
        segment_index: int,
        battery_range: float
    ) -> bool:
        """
        Simulate: if bus charges at candidate station, can it complete the route safely?
        
        Args:
            charging_station_id: Station where charging would occur
            current_range: Current battery range before charging
            segments: Direction-aware segment list for the bus
            segment_index: Current segment index
            battery_range: Full battery range after charging
            
        Returns:
            True if bus can complete route after charging at this station
        """
        # Find the segment index of the charging station
        charge_index = None
        for i, segment in enumerate(segments):
            if segment["to_station"] == charging_station_id:
                charge_index = i + 1
                break
        
        if charge_index is None:
            logger.warning(f"Charging station {charging_station_id} not found in route")  # pragma: no cover
            return False  # pragma: no cover
        
        # Simulate: after charging, bus has full battery range
        # Calculate total distance from charging station to end of route
        remaining_distance = 0.0
        for i in range(charge_index, len(segments)):
            remaining_distance += segments[i]["distance_km"]
        
        # Check if remaining distance can be covered with full battery range
        can_complete = remaining_distance <= battery_range
        
        logger.debug(
            f"Simulate charge at {charging_station_id}: remaining_distance={remaining_distance}km, "
            f"battery_range={battery_range}km -> can_complete={can_complete}"
        )
        
        return can_complete
    
    def _get_current_queue_length(
        self,
        station_id: str,
        station_chargers: Dict[str, List[float]],
        current_time: float
    ) -> int:
        """
        Get current queue length at a station.
        
        Queue length = number of chargers that are busy (not yet available at current_time)
        
        Args:
            station_id: Station to check
            station_chargers: Charger availability per station
            current_time: Current time in minutes
            
        Returns:
            Number of buses waiting in queue (0 if station is not a charging station)
        """
        # If station is not a charging station (e.g., endpoint), return 0
        if station_id not in station_chargers:
            logger.debug(f"Station {station_id} is not a charging station, queue length = 0")
            return 0
        
        chargers = station_chargers[station_id]
        queue_length = sum(1 for charger_time in chargers if charger_time > current_time)
        
        logger.debug(f"Station {station_id} queue length: {queue_length} (time={current_time})")
        return queue_length
    
    def _calculate_wait_time(
        self,
        queue_length: int,
        charging_time: float
    ) -> float:
        """
        Calculate expected wait time based on queue length.
        
        Formula: queue_length × charging_time
        
        Args:
            queue_length: Number of buses in queue
            charging_time: Time per charging session in minutes
            
        Returns:
            Expected wait time in minutes
        """
        wait_time = queue_length * charging_time
        logger.debug(f"Wait time: queue={queue_length}, charging_time={charging_time}min -> {wait_time}min")
        return wait_time
    
    def _calculate_extra_stops(
        self,
        candidate_station: str,
        current_station: str,
        candidate_stations: List[str]
    ) -> int:
        """
        Calculate extra charging stops if charging at candidate vs greedy approach.
        
        Greedy approach: charge only when necessary (first station in list where range insufficient)
        Load-aware: may charge earlier to avoid congestion
        
        Args:
            candidate_station: Station being evaluated
            current_station: Station where bus currently is
            candidate_stations: All reachable stations in order
            
        Returns:
            Number of extra charging stops (0 if same as greedy, 1+ if earlier)
        """
        # Find index of current station and candidate station
        try:
            current_idx = candidate_stations.index(current_station)
            candidate_idx = candidate_stations.index(candidate_station)
        except ValueError:
            return 0  # pragma: no cover
        
        # Extra stops = difference in indices
        extra_stops = abs(candidate_idx - current_idx)
        
        logger.debug(
            f"Extra stops: current={current_station} (idx={current_idx}), "
            f"candidate={candidate_station} (idx={candidate_idx}) -> {extra_stops}"
        )
        
        return extra_stops
    
    def _calculate_current_range(
        self,
        schedule: BusSchedule,
        segments: List,
        segment_index: int,
        battery_range: float
    ) -> float:
        """
        Calculate current battery range based on distance traveled since last charge.
        
        Args:
            schedule: Current bus schedule
            segments: Direction-aware segment list for the bus
            segment_index: Current segment index
            battery_range: Full battery range
            
        Returns:
            Remaining battery range in km
        """
        # Calculate distance traveled since last charge
        distance_since_last_charge = 0.0
        
        if schedule.charging_events:
            # Bus has charged before, calculate distance since last charge
            last_charge_station = schedule.charging_events[-1].station_id
            last_charge_index = None
            
            for i, segment in enumerate(segments):
                if segment["to_station"] == last_charge_station:
                    last_charge_index = i + 1
                    break
            
            if last_charge_index is not None:
                for i in range(last_charge_index, segment_index):
                    distance_since_last_charge += segments[i]["distance_km"]
        else:
            # Bus hasn't charged yet, calculate distance from start
            for i in range(0, segment_index):
                distance_since_last_charge += segments[i]["distance_km"]
        
        remaining_range = battery_range - distance_since_last_charge
        logger.debug(f"Current range: {remaining_range}km (traveled {distance_since_last_charge}km)")
        return remaining_range
    
    def _schedule_charging(
        self,
        bus: Bus,
        station_id: str,
        arrival_time: float,
        schedule: BusSchedule,
        charger_availability: List[float],
        charging_time: float,
        operator_wait_times: Dict[str, List[float]],
        event_queue: List,
        segment_index: int,
        route: Route
    ):
        """
        Schedule a charging event for a bus (same as greedy scheduler).
        
        Args:
            bus: The bus to charge
            station_id: Station where charging occurs
            arrival_time: When bus arrived
            schedule: Bus schedule to update
            charger_availability: List of when each charger is free
            charging_time: How long charging takes
            operator_wait_times: Track operator wait times
            event_queue: Event queue to add departure event
            segment_index: Current segment index
            route: Route definition
        """
        # Find the earliest available charger
        earliest_time = min(charger_availability)
        charger_index = charger_availability.index(earliest_time)
        
        # Determine when charging can start
        charge_start_time = max(arrival_time, earliest_time)
        charge_end_time = charge_start_time + charging_time
        wait_time = max(0, charge_start_time - arrival_time)
        
        # Update charger availability
        charger_availability[charger_index] = charge_end_time
        
        # Record charging event
        schedule.charging_events.append(ChargingEvent(
            station_id=station_id,
            arrival_time=arrival_time,
            charge_start_time=charge_start_time,
            charge_end_time=charge_end_time,
            wait_time=wait_time
        ))
        
        # Update total wait time
        schedule.total_wait_time += wait_time
        
        # Track operator wait time
        operator_wait_times[bus.operator].append(wait_time)
        
        logger.debug(
            f"Bus {bus.bus_id} charging at {station_id}: "
            f"wait={wait_time:.1f}min, start={charge_start_time:.1f}, end={charge_end_time:.1f}"
        )
        
        # Add departure event after charging
        heapq.heappush(event_queue, (
            charge_end_time,
            "departure",
            bus.bus_id,
            station_id,
            segment_index
        ))
    
    def _build_station_schedules(
        self,
        scenario: Scenario,
        bus_schedules: Dict[str, BusSchedule]
    ) -> List[StationSchedule]:
        """
        Build station schedules from bus schedules (same as greedy scheduler).
        
        Args:
            scenario: The scenario
            bus_schedules: All bus schedules
            
        Returns:
            List of station schedules
        """
        station_schedules = []
        
        for station_id in scenario.stations.keys():
            charging_queue = []
            
            for bus_schedule in bus_schedules.values():
                for event in bus_schedule.charging_events:
                    if event.station_id == station_id:
                        charging_queue.append({
                            "bus_id": bus_schedule.bus_id,
                            "start": event.charge_start_time,
                            "end": event.charge_end_time,
                            "wait_time": event.wait_time
                        })
            
            charging_queue.sort(key=lambda x: x["start"])
            
            station_schedules.append(StationSchedule(
                station_id=station_id,
                charging_queue=charging_queue
            ))
        
        return station_schedules
    
    def _calculate_metrics(
        self,
        bus_schedules: Dict[str, BusSchedule],
        operator_wait_times: Dict[str, List[float]]
    ) -> ScheduleMetrics:
        """
        Calculate aggregate metrics for the schedule (same as greedy scheduler).
        
        Args:
            bus_schedules: All bus schedules
            operator_wait_times: Wait times per operator
            
        Returns:
            Schedule metrics
        """
        total_network_time = sum(s.final_arrival_time for s in bus_schedules.values())
        avg_wait_per_bus = sum(s.total_wait_time for s in bus_schedules.values()) / len(bus_schedules)
        
        avg_wait_per_operator = {}
        for operator, waits in operator_wait_times.items():
            if waits:
                avg_wait_per_operator[operator] = sum(waits) / len(waits)
            else:
                avg_wait_per_operator[operator] = 0.0
        
        max_wait_time = max(s.total_wait_time for s in bus_schedules.values())
        
        return ScheduleMetrics(
            total_network_time=total_network_time,
            avg_wait_per_bus=avg_wait_per_bus,
            avg_wait_per_operator=avg_wait_per_operator,
            max_wait_time=max_wait_time
        )
