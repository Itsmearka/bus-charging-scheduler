"""
Solution Extraction Module
Handles extraction of charging plans from CP-SAT solver solution.
"""

from typing import Dict, List
from ortools.sat.python import cp_model
from src.models import ChargingPlan, ChargingEvent
from src.utils.route import get_route_stations_in_order
from src.utils.time import calculate_travel_time


class SolutionExtractor:
    """
    Extracts charging plans from solver solution.
    """
    
    def __init__(self, solver: cp_model.CpSolver, variables: Dict, config: dict):
        """
        Initialize solution extractor.
        
        Args:
            solver: CP-SAT solver
            variables: Dictionary of decision variables
            config: Configuration dictionary
        """
        self.solver = solver
        self.variables = variables
        self.config = config
    
    def extract_solution(self, buses: List) -> List[ChargingPlan]:
        """
        Extract charging plans from the solver solution.
        
        Args:
            buses: List of Bus objects
        
        Returns:
            List of ChargingPlan objects
        """
        plans = []
        
        for bus in buses:
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
