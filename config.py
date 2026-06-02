"""
Configuration file for Bus Charging Scheduler.
This is the single source of truth for all configurable values.

To modify any value:
1. Edit the constant below
2. Restart the Streamlit app
3. All scenarios will use the new value unless they override it
"""

from typing import Dict, List, Tuple

# Physical constants - battery and charging
BATTERY_RANGE_KM: int = 240
"""Maximum distance a bus can travel on a full charge (in kilometers)"""

CHARGING_TIME_MINUTES: int = 25
"""Time required to fully charge a bus (in minutes)"""

BUS_SPEED_KMH: int = 60
"""Average bus speed (in km/h). Used to calculate travel time."""

# Route definition - Bengaluru to Kochi
# Format: List of (from_location, to_location, distance_km)
ROUTE_SEGMENTS: List[Tuple[str, str, int]] = [
    ("Bengaluru", "A", 100),
    ("A", "B", 120),
    ("B", "C", 100),
    ("C", "D", 120),
    ("D", "Kochi", 100),
]
"""Route segments with distances. Total: 540 km"""

# Charging stations (excludes endpoints Bengaluru and Kochi)
STATIONS: List[str] = ["A", "B", "C", "D"]
"""List of charging stations along the route"""

# Charger capacity per station
CHARGERS_PER_STATION: Dict[str, int] = {
    "A": 1,
    "B": 1,
    "C": 1,
    "D": 1,
}
"""Number of chargers at each station. One bus per charger at a time."""

# Default optimization weights
DEFAULT_WEIGHTS: Dict[str, float] = {
    "individual": 1.0,  # Minimize wait time for individual buses
    "operator": 1.0,    # Minimize delays across operator fleets
    "overall": 1.0,     # Minimize total system time
}
"""
Weights for the objective function.
Higher weight = more importance in optimization.
Can be overridden per scenario.
"""

# Dynamic Bus Generation Defaults
DEFAULT_BUS_FORWARD: int = 10
"""Default number of forward (Bengaluru→Kochi) buses for dynamic generation"""

DEFAULT_BUS_REVERSE: int = 10
"""Default number of reverse (Kochi→Bengaluru) buses for dynamic generation"""

DEFAULT_START_TIME_FORWARD: str = "19:00"
"""Default start time for forward buses (HH:MM format)"""

DEFAULT_START_TIME_REVERSE: str = "19:00"
"""Default start time for reverse buses (HH:MM format)"""

DEFAULT_DEPARTURE_INTERVAL_MINUTES: int = 15
"""Default departure interval between consecutive buses (in minutes)"""

OPERATORS: List[str] = ["kpn", "freshbus", "flixbus"]
"""List of available operators for bus assignment"""

# Optimization settings (Phase 2)
ENABLE_OPTIMIZATIONS: bool = False
"""
Toggle Phase 2 optimizations (time-window decomposition, station filtering).
Set to True for scenarios with 40+ buses.
Set to False for standard scenarios (20-40 buses).
"""

TIME_WINDOW_THRESHOLD_MINUTES: int = 30
"""
For Phase 2 optimizations: buses arriving >30 minutes apart at a station
don't need ordering constraints (can't conflict).
"""

SOLVER_TIME_LIMIT_SECONDS: int = 60
"""
Maximum time for CP-SAT solver to run.
Reduced to 60 seconds for faster FEASIBLE solutions on large scenarios.
Use 300 seconds for optimal solutions on smaller scenarios.
"""

# Derived constants (do not modify)
TOTAL_ROUTE_DISTANCE_KM: int = sum(seg[2] for seg in ROUTE_SEGMENTS)
"""Total route distance: 540 km"""

STATION_LOCATIONS_KM: Dict[str, int] = {}
"""Distance of each station from Bengaluru (calculated automatically)"""

# Calculate station locations
_distance = 0
for from_loc, to_loc, dist in ROUTE_SEGMENTS:
    if to_loc in STATIONS:
        _distance += dist
        STATION_LOCATIONS_KM[to_loc] = _distance
    elif from_loc in STATIONS and from_loc not in STATION_LOCATIONS_KM:
        STATION_LOCATIONS_KM[from_loc] = _distance
        _distance += dist
    else:
        _distance += dist
