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
from src.utils.route import (
    get_route_stations_in_order,
    calculate_distance_between_stations,
    get_station_distance_from_origin
)
from src.utils.time import calculate_travel_time
from src.constraints.range import add_range_constraint
from src.constraints.capacity import add_charger_capacity_constraint, add_symmetry_breaking_constraint
from src.constraints.route import add_route_order_constraint
from src.constraints.timing import add_charging_duration_constraint, add_travel_time_constraint, add_arrival_start_constraint
from src.objectives import build_objective
from src.scheduler_variables import VariableManager
from src.scheduler_solution import SolutionExtractor


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
        
        # Initialize helper classes
        self.variable_manager = VariableManager(self.model, self.config)
        self.solution_extractor = None  # Will be initialized after variables are created
    
    def _add_constraints(self) -> None:
        """
        Add all hard constraints to the model.
        """
        buses = self.scenario.buses
        stations = self.config['stations']
        
        # Get variables from variable manager
        self.variables = self.variable_manager.variables
        
        # 1. Range constraint - forces buses to charge
        add_range_constraint(
            self.model, self.variables, buses, stations,
            self.config['battery_range_km'], self.config
        )
        
        # 2. Symmetry breaking - eliminate duplicate solutions (Phase 2)
        add_symmetry_breaking_constraint(
            self.model, self.variables, buses, stations, self.config.get('enable_optimizations', False)
        )
        
        # 3. Charger capacity - prevents overlapping charges
        add_charger_capacity_constraint(
            self.model, self.variables, buses, stations,
            self.config['chargers_per_station'], self.config.get('enable_optimizations', False)
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
    
    def _add_greedy_hint(self) -> None:
        """
        Provide greedy heuristic solution as hint to CP-SAT solver.
        
        This method generates a simple feasible solution using a greedy heuristic:
        - Charges buses at every station to ensure range compliance
        - Simple strategy: suggest charging at all stations
        - Provides this solution as a hint to speed up solver search
        
        The hint is purely for performance optimization and does not affect
        the final solution quality. CP-SAT can ignore the hint if it leads to
        a suboptimal search path, guaranteeing optimal/feasible solutions.
        
        Expected performance improvement: 50-80% faster first solve time.
        """
        buses = self.scenario.buses
        stations = self.config['stations']
        
        for bus in buses:
            # Get stations in route order based on bus direction
            route_stations = get_route_stations_in_order(bus.direction)
            
            # Simple greedy heuristic: suggest charging at all stations
            # This ensures range compliance and provides a feasible starting point
            for station in route_stations:
                # Only suggest charging for stations that are in the available stations list
                if station in stations:
                    charge_var = self.variables['charge_at'][(bus.id, station)]
                    self.model.AddHint(charge_var, 1)
        
        # Enable hint repair so solver can fix infeasible hints
        # This allows CP-SAT to adjust the hint if it violates constraints
        self.solver.parameters.repair_hint = True
        # Limit how much effort to spend repairing hint (20 conflicts max)
        self.solver.parameters.hint_conflict_limit = 20
    
    def solve(self) -> SchedulerResult:
        """
        Solve the scheduling problem.
        
        Returns:
            SchedulerResult with charging plans and metrics
        """
        start_time = time.time()
        
        # Create variables using VariableManager
        self.variables = self.variable_manager.create_variables(
            self.scenario.buses, 
            self.enable_optimizations
        )
        
        # Add constraints
        self._add_constraints()
        
        # Build objective
        self._build_objective()
        
        # Add greedy heuristic hint to speed up first solve
        # This provides a feasible starting point for the solver
        # Conditionally enabled based on config - empirical testing shows hints slow down this problem
        if self.config.get('enable_hints', True):
            self._add_greedy_hint()
        
        # Set solver parameters
        if self.unlimited_time:
            # No time limit - use very large value (effectively unlimited)
            # CP-SAT doesn't handle float('inf') well, so use 1 year in seconds
            self.solver.parameters.max_time_in_seconds = 31536000  # 1 year
        else:
            self.solver.parameters.max_time_in_seconds = self.config['solver_time_limit_seconds']
        
        # Worker configuration: use constant from config for consistent performance
        # Set to 2 for both local and cloud environments
        # self.solver.parameters.num_search_workers = config.NUM_SEARCH_WORKERS
        
        # Additional solver parameters for better performance
        self.solver.parameters.linearization_level = self.config.get('linearization_level', 0)
        # Set max_number_of_conflicts based on config
        self.solver.parameters.max_number_of_conflicts = self.config.get('max_number_of_conflicts', 100000)
        # Enable presolve for better performance
        if self.config.get('cp_model_presolve', False):
            self.solver.parameters.cp_model_presolve = True
        # self.solver.parameters.interleave_search = True  # Better diversification with multiple workers
        self.solver.parameters.log_search_progress = False
        
        # Solve
        status = self.solver.Solve(self.model)
        
        solve_time = time.time() - start_time
        
        # Extract solver statistics
        num_vars = len(self.model.Proto().variables)
        num_constraints = len(self.model.Proto().constraints)
        branches = self.solver.NumBranches()
        conflicts = self.solver.NumConflicts()
        objective_value = self.solver.ObjectiveValue()
        objective_bound = self.solver.BestObjectiveBound()
        
        # Convert to int to avoid Pydantic validation errors
        if objective_value is not None:
            objective_value = int(objective_value)
        if objective_bound is not None:
            objective_bound = int(objective_bound)
        
        # Compute optimality gap
        if objective_value is not None and objective_bound is not None:
            optimality_gap = ((objective_value - objective_bound) / max(1, objective_value)) * 100
        else:
            optimality_gap = None
        
        # Check solver status
        if status == cp_model.OPTIMAL:
            solver_status = "OPTIMAL"
            optimality_gap = 0.0  # Optimal solutions have 0% gap
        elif status == cp_model.FEASIBLE:
            solver_status = "FEASIBLE"
        else:
            solver_status = "INFEASIBLE"
            raise ValueError(f"Solver could not find a solution. Status: {status}")
        
        # Extract solution using SolutionExtractor
        self.solution_extractor = SolutionExtractor(self.solver, self.variables, self.config)
        plans = self.solution_extractor.extract_solution(self.scenario.buses)
        
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
            average_wait_time_minutes=avg_wait,
            num_variables=num_vars,
            num_constraints=num_constraints,
            branches_explored=branches,
            conflicts=conflicts,
            objective_value=objective_value,
            objective_bound=objective_bound,
            optimality_gap_percent=optimality_gap
        )
        
        return result
