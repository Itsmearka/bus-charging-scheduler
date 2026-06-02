"""
Bus Charging Scheduler - CP-SAT engine.
Core scheduler that uses constraint programming to optimize charging plans.
"""

import time
from typing import Dict, List, Tuple
from ortools.sat.python import cp_model
import config
from src.models import Scenario, SchedulerResult, ChargingPlan, ChargingEvent
from src.loader import get_scenario_config
from src.utils import (
    get_route_stations_in_order,
    calculate_distance_between_stations,
    calculate_travel_time,
    get_station_distance_from_origin
)
from src.constraints import (
    add_range_constraint,
    add_charger_capacity_constraint,
    add_route_order_constraint,
    add_charging_duration_constraint,
    add_travel_time_constraint,
    add_arrival_start_constraint
)
from src.objectives import build_objective


class BusChargingScheduler:
    """
    Main scheduler class using CP-SAT constraint programming.
    """
    
    def __init__(self, scenario: Scenario, enable_optimizations: bool = False, unlimited_time: bool = False):
        """
        Initialize the scheduler with a scenario.
        
        Args:
            scenario: Scenario object with buses and configuration
            enable_optimizations: Whether to use Phase 2 optimizations
            unlimited_time: Whether to disable solver time limit
        """
        self.scenario = scenario
        self.enable_optimizations = enable_optimizations
        self.unlimited_time = unlimited_time
        
        # Get effective configuration (merge scenario overrides with global config)
        self.config = get_scenario_config(scenario)
        
        # Initialize CP-SAT model and solver
        self.model = cp_model.CpModel()
        self.solver = cp_model.CpSolver()
        
        # Decision variables dictionary
        self.variables = {}
        
    def _create_variables(self) -> None:
        """
        Create all decision variables for the CP-SAT model.
        """
        buses = self.scenario.buses
        stations = self.config['stations']
        
        # Initialize variable dictionaries
        self.variables['charge_at'] = {}
        self.variables['arrival_time'] = {}
        self.variables['start_time'] = {}
        self.variables['end_time'] = {}
        self.variables['wait_time'] = {}
        self.variables['order'] = {}
        
        # For each bus and station, create variables
        for bus in buses:
            for station in stations:
                # Binary variable: does this bus charge at this station?
                self.variables['charge_at'][(bus.id, station)] = self.model.NewBoolVar(
                    f"charge_{bus.id}_{station}"
                )
                
                # Integer variable: arrival time at this station (in minutes from midnight)
                # Phase 2 optimization: use pre-computed bounds to tighten domain
                if self.enable_optimizations:
                    min_arrival, max_arrival = self._compute_arrival_bounds(bus, station)
                    self.variables['arrival_time'][(bus.id, station)] = self.model.NewIntVar(
                        min_arrival, max_arrival, f"arrival_{bus.id}_{station}"
                    )
                else:
                    # Upper bound: generous estimate (48 hours = 2880 minutes)
                    self.variables['arrival_time'][(bus.id, station)] = self.model.NewIntVar(
                        0, 2880, f"arrival_{bus.id}_{station}"
                    )
                
                # Integer variable: charging start time
                self.variables['start_time'][(bus.id, station)] = self.model.NewIntVar(
                    0, 2880, f"start_{bus.id}_{station}"
                )
                
                # Integer variable: charging end time
                self.variables['end_time'][(bus.id, station)] = self.model.NewIntVar(
                    0, 2880, f"end_{bus.id}_{station}"
                )
                
                # Integer variable: wait time at this station
                self.variables['wait_time'][(bus.id, station)] = self.model.NewIntVar(
                    0, 1440, f"wait_{bus.id}_{station}"
                )
        
        # Create ordering variables for charger capacity constraints
        for station in stations:
            buses_at_station = [bus for bus in buses]
            for i in range(len(buses_at_station)):
                for j in range(i + 1, len(buses_at_station)):
                    bus_i = buses_at_station[i]
                    bus_j = buses_at_station[j]
                    
                    # Binary variable: does bus_i charge before bus_j at this station?
                    self.variables['order'][(bus_i.id, bus_j.id, station)] = self.model.NewBoolVar(
                        f"order_{bus_i.id}_{bus_j.id}_{station}"
                    )
        
        # Create final arrival time variable for each bus
        self.variables['arrival_time_final'] = {}
        for bus in buses:
            self.variables['arrival_time_final'][bus.id] = self.model.NewIntVar(
                0, 2880, f"arrival_final_{bus.id}"
            )
    
    def _compute_arrival_bounds(self, bus, station):
        """
        Compute min/max possible arrival time for a bus at a station.
        
        Args:
            bus: Bus object
            station: Station ID
        
        Returns:
            Tuple of (min_arrival, max_arrival) in minutes from midnight
        """
        from src.utils import get_station_distance_from_origin
        
        # Calculate earliest arrival (direct travel, no charging)
        distance = get_station_distance_from_origin(station, bus.direction)
        travel_time = int((distance / self.config['bus_speed_kmh']) * 60)
        min_arrival = bus.departure_time_minutes + travel_time
        
        # Calculate latest arrival (worst case: charge at all previous stations)
        stations_in_order = [s for s in self.config['stations'] if s != station]
        # Filter to only stations before this one in route
        from src.utils import get_route_stations_in_order
        route_stations = get_route_stations_in_order(bus.direction)
        prev_stations = []
        for s in route_stations:
            if s == station:
                break
            if s in stations_in_order:
                prev_stations.append(s)
        
        # Add charging time for all previous stations
        max_arrival = min_arrival + len(prev_stations) * self.config['charging_time_minutes']
        
        # Add buffer for possible waiting (up to 2 hours per station)
        max_arrival += len(prev_stations) * 120
        
        return min_arrival, max_arrival
    
    def _add_constraints(self) -> None:
        """
        Add all hard constraints to the model.
        """
        buses = self.scenario.buses
        stations = self.config['stations']
        
        # 1. Range constraint - forces buses to charge
        add_range_constraint(
            self.model, self.variables, buses, stations,
            self.config['battery_range_km'], self.config
        )
        
        # 2. Symmetry breaking - eliminate duplicate solutions (Phase 2)
        from src.constraints import add_symmetry_breaking_constraint
        add_symmetry_breaking_constraint(
            self.model, self.variables, buses, stations, self.enable_optimizations
        )
        
        # 3. Charger capacity - prevents overlapping charges
        add_charger_capacity_constraint(
            self.model, self.variables, buses, stations,
            self.config['chargers_per_station'], self.enable_optimizations
        )
        
        # 4. Route order - no backtracking
        add_route_order_constraint(
            self.model, self.variables, buses, stations
        )
        
        # 5. Charging duration - fixed charge time
        add_charging_duration_constraint(
            self.model, self.variables, buses, stations,
            self.config['charging_time_minutes']
        )
        
        # 5. Travel time - correct arrival times
        add_travel_time_constraint(
            self.model, self.variables, buses, stations,
            self.config['bus_speed_kmh'], self.config
        )
        
        # 6. Arrival before start - can't charge before arriving
        add_arrival_start_constraint(
            self.model, self.variables, buses, stations
        )
        
        # 7. Wait time calculation
        for bus in buses:
            for station in stations:
                arrival = self.variables['arrival_time'][(bus.id, station)]
                start = self.variables['start_time'][(bus.id, station)]
                wait = self.variables['wait_time'][(bus.id, station)]
                charge = self.variables['charge_at'][(bus.id, station)]
                
                self.model.Add(wait == start - arrival).OnlyEnforceIf(charge)
                self.model.Add(wait == 0).OnlyEnforceIf(charge.Not())
    
    def _build_objective(self) -> None:
        """
        Build the weighted objective function.
        """
        objective = build_objective(
            self.model, self.variables,
            self.scenario.buses, self.config['stations'],
            self.config['weights']
        )
        self.model.Minimize(objective)
    
    def solve(self) -> SchedulerResult:
        """
        Solve the scheduling problem.
        
        Returns:
            SchedulerResult with charging plans and metrics
        """
        start_time = time.time()
        
        # Create variables
        self._create_variables()
        
        # Add constraints
        self._add_constraints()
        
        # Build objective
        self._build_objective()
        
        # Set solver parameters
        if self.unlimited_time:
            # No time limit - use very large value (effectively unlimited)
            # CP-SAT doesn't handle float('inf') well, so use 1 year in seconds
            self.solver.parameters.max_time_in_seconds = 31536000  # 1 year
        else:
            self.solver.parameters.max_time_in_seconds = self.config['solver_time_limit_seconds']
        self.solver.parameters.num_search_workers = 8  # Recommended by OR-Tools for parallel search
        self.solver.parameters.log_search_progress = False
        
        # Solve
        status = self.solver.Solve(self.model)
        
        solve_time = time.time() - start_time
        
        # Check solver status
        if status == cp_model.OPTIMAL:
            solver_status = "OPTIMAL"
        elif status == cp_model.FEASIBLE:
            solver_status = "FEASIBLE"
        else:
            solver_status = "INFEASIBLE"
            raise ValueError(f"Solver could not find a solution. Status: {status}")
        
        # Extract solution
        plans = self._extract_solution()
        
        # Calculate metrics
        total_wait = sum(plan.total_wait_time_minutes for plan in plans)
        max_wait = max(plan.total_wait_time_minutes for plan in plans) if plans else 0
        avg_wait = total_wait / len(plans) if plans else 0
        
        # Create result
        result = SchedulerResult(
            scenario_name=self.scenario.name,
            plans=plans,
            solve_time_seconds=solve_time,
            optimization_enabled=self.enable_optimizations,
            solver_status=solver_status,
            total_wait_time_minutes=total_wait,
            max_wait_time_minutes=max_wait,
            average_wait_time_minutes=avg_wait
        )
        
        return result
    
    def _extract_solution(self) -> List[ChargingPlan]:
        """
        Extract charging plans from the solver solution.
        
        Returns:
            List of ChargingPlan objects
        """
        plans = []
        
        for bus in self.scenario.buses:
            events = []
            stations_in_order = get_route_stations_in_order(bus.direction)
            
            for station in stations_in_order:
                # Check if bus charges at this station
                charge_var = self.variables['charge_at'][(bus.id, station)]
                if self.solver.Value(charge_var) == 1:
                    # Extract charging event details
                    arrival = self.solver.Value(self.variables['arrival_time'][(bus.id, station)])
                    start = self.solver.Value(self.variables['start_time'][(bus.id, station)])
                    end = self.solver.Value(self.variables['end_time'][(bus.id, station)])
                    wait = self.solver.Value(self.variables['wait_time'][(bus.id, station)])
                    
                    event = ChargingEvent(
                        bus_id=bus.id,
                        station_id=station,
                        arrival_time_minutes=arrival,
                        start_time_minutes=start,
                        end_time_minutes=end,
                        wait_time_minutes=wait
                    )
                    events.append(event)
            
            # Calculate final arrival time (simplified)
            final_arrival = bus.departure_time_minutes + calculate_travel_time(
                self.config['total_route_distance_km'], self.config['bus_speed_kmh']
            )
            
            # Calculate total wait time
            total_wait = sum(event.wait_time_minutes for event in events)
            
            # Create charging plan
            plan = ChargingPlan(
                bus_id=bus.id,
                events=events,
                total_wait_time_minutes=total_wait,
                arrival_time_minutes=final_arrival,
                departure_time_minutes=bus.departure_time_minutes
            )
            plans.append(plan)
        
        return plans
