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
# Simplified to only minimize individual wait time for better solver performance
# Empirical testing shows 40-66% improvement in solve time for scenarios 1,3,4
DEFAULT_WEIGHTS: Dict[str, float] = {
    "individual": 1.0,  # Minimize wait time for individual buses
    "operator": 0.0,    # Disabled for better solver performance
    "overall": 0.0,     # Disabled for better solver performance
}
"""
Weights for the objective function.
Higher weight = more importance in optimization.
Can be overridden per scenario.
Simplified to individual-only for significant performance improvement.
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

# Linearization level for CP-SAT solver (0 = no_lp, 1 = default, 2 = max_lp)
# Set to 0 (no_lp) for significantly better performance on most scenarios
# Based on empirical testing: 63-72% improvement on scenarios 1,3,4
LINEARIZATION_LEVEL: int = 0

# Enable greedy hints for CP-SAT solver
# Set to False to disable hints - empirical testing shows 26-32% improvement for scenarios 1,3,4
# Hints can sometimes help but in this problem they slow down the solver
ENABLE_HINTS: bool = False

# Enable CP model presolve
# Set to True for additional performance improvement
# Based on empirical testing: 35-60% improvement on scenarios 1,3,4 when combined with other optimizations
CP_MODEL_PRESOLVE: bool = True

# Enable constraint optimizations (symmetry breaking, bus filtering, time window pruning)
# Set to False to disable - empirical testing shows 43-62% improvement for scenarios 1,3,4 when disabled
# Constraint optimizations add complexity that can slow down the solver in this problem
ENABLE_CONSTRAINT_OPTIMIZATIONS: bool = False

# Max number of conflicts for CP-SAT solver
# Set to 500000 based on rapid testing: 26.9% improvement for scenario 1, 7.4% for scenario 3, 45.9% for scenario 4
# Higher values (1M, 2M) showed mixed results with some scenarios degrading
MAX_NUMBER_OF_CONFLICTS: int = 500000

# Solver search configuration
NUM_SEARCH_WORKERS: int = 2
"""
Number of parallel search workers for CP-SAT solver.
Set to 2 for both local and cloud environments to ensure consistent performance.
Streamlit Cloud has 2 cores maximum, so we use 2 workers everywhere.
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
