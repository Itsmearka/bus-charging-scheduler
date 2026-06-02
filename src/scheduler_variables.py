"""
Variable Management Module
Handles creation of CP-SAT decision variables for the scheduler.
"""

from typing import Dict, List, Tuple
from ortools.sat.python import cp_model


class VariableManager:
    """
    Manages creation of CP-SAT decision variables.
    """
    
    def __init__(self, model: cp_model.CpModel, config: dict):
        """
        Initialize variable manager.
        
        Args:
            model: CP-SAT model
            config: Configuration dictionary
        """
        self.model = model
        self.config = config
        self.variables = {}
    
    def create_variables(self, buses: List, enable_optimizations: bool) -> Dict:
        """
        Create all decision variables for the CP-SAT model.
        
        Args:
            buses: List of Bus objects
            enable_optimizations: Whether to use Phase 2 optimizations
        
        Returns:
            Dictionary of decision variables
        """
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
                if enable_optimizations:
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
        
        return self.variables
    
    def _compute_arrival_bounds(self, bus, station: str) -> Tuple[int, int]:
        """
        Compute min/max possible arrival time for a bus at a station.
        
        Args:
            bus: Bus object
            station: Station ID
        
        Returns:
            Tuple of (min_arrival, max_arrival) in minutes from midnight
        """
        from src.utils.route import get_station_distance_from_origin, get_route_stations_in_order
        
        # Calculate earliest arrival (direct travel, no charging)
        distance = get_station_distance_from_origin(station, bus.direction)
        travel_time = int((distance / self.config['bus_speed_kmh']) * 60)
        min_arrival = bus.departure_time_minutes + travel_time
        
        # Calculate latest arrival (worst case: charge at all previous stations)
        stations_in_order = [s for s in self.config['stations'] if s != station]
        # Filter to only stations before this one in route
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
