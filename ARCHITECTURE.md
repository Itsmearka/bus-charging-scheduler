# Architecture

This document provides detailed architectural decisions, design rationale, and extensibility guidelines for the Bus Charging Scheduler.

## Framework/Approach Choice and Justification

### Constraint Programming with CP-SAT

The scheduler uses Google OR-Tools' CP-SAT (Constraint Programming - SATisfiability) solver, which is well-suited for this problem for several reasons:

**Why CP-SAT Fits:**
- **Discrete Decision Variables**: The problem involves discrete decisions (which charger each bus uses at which station and at what time), which CP-SAT handles natively
- **Complex Constraints**: Charging schedules must satisfy multiple interdependent constraints (range, capacity, ordering, travel time) that are naturally expressed as logical constraints
- **Optimization Objectives**: The weighted objective (minimizing individual wait times, operator fairness, and overall system efficiency) is directly supported
- **Deterministic Results**: Unlike heuristic approaches, CP-SAT guarantees optimal or near-optimal solutions within time limits
- **Scalability**: CP-SAT can handle hundreds of variables and thousands of constraints efficiently

**Alternative Approaches Considered:**
- **Linear Programming (LP)**: Would require linearizing discrete decisions, losing precision and requiring complex integer programming extensions
- **Heuristic Algorithms (Genetic, Simulated Annealing)**: No guarantee of optimality, difficult to tune, and harder to validate correctness
- **Custom Greedy Algorithm**: Would be brittle, hard to maintain, and unlikely to find optimal solutions for complex scenarios

**Why CP-SAT Specifically:**
- Mature, production-ready library from Google
- Excellent Python API with clear documentation
- Built-in support for multi-objective optimization
- Parallel search capabilities for faster solve times
- Active community support and ongoing development

## Data Structure Design

### Core Models (Pydantic)

The data models use Pydantic for type safety, validation, and serialization:

```python
# Bus: Represents a single bus with its schedule
Bus(id: str, operator: str, direction: str, departure_time_minutes: int)

# Scenario: Contains all buses and configuration
Scenario(name: str, buses: List[Bus], weights: Dict[str, float])

# ChargingEvent: Represents a single charging session
ChargingEvent(bus_id: str, station_id: str, arrival_time_minutes: int, 
              start_time_minutes: int, end_time_minutes: int, wait_time_minutes: int)
```

**Design Rationale:**
- **Pydantic Models**: Automatic validation ensures data integrity throughout the application
- **Immutable by Default**: Prevents accidental modifications that could corrupt the state
- **JSON Serialization**: Easy to save/load scenarios from files
- **Type Hints**: IDE support and early error detection

### Decision Variables (CP-SAT)

The solver uses the following decision variables:

```python
# charge_at[(bus_id, station)]: Boolean - does bus charge at station?
# start_time[(bus_id, station)]: Integer - when does charging start?
# end_time[(bus_id, station)]: Integer - when does charging end?
# arrival_time[(bus_id, station)]: Integer - when does bus arrive?
```

**Design Rationale:**
- **Sparse Variables**: Only create variables for feasible (bus, station) pairs
- **Integer Time Variables**: Time expressed in minutes from midnight (0-1440) for easy arithmetic
- **Boolean Charge Variables**: Simple on/off decisions for charging at each station

### Configuration (config.py)

All physical constants and solver parameters are centralized:

```python
BATTERY_RANGE_KM = 240
CHARGING_TIME_MINUTES = 25
BUS_SPEED_KMH = 60
SOLVER_TIME_LIMIT_SECONDS = 60
```

**Design Rationale:**
- **Single Source of Truth**: Easy to modify parameters without hunting through code
- **No Magic Numbers**: All constants have meaningful names
- **Easy Tuning**: Solver parameters can be adjusted for performance optimization

## Anticipated Future Changes and Design Handling

### 1. Adding More Charging Stations

**Change:** Add new stations along the route (e.g., station E between C and D)

**How Design Handles It:**
- Update `config.ROUTE_SEGMENTS` to include the new segment
- Add station to `config.STATIONS` list
- Update `config.CHARGERS_PER_STATION` with capacity for new station
- No code changes required in scheduler - it dynamically handles any number of stations

```python
# config.py
ROUTE_SEGMENTS = [
    ("Bengaluru", "A", 100),
    ("A", "B", 120),
    ("B", "C", 100),
    ("C", "E", 80),      # New station
    ("E", "D", 40),      # New segment
    ("D", "Kochi", 100),
]

STATIONS = ["A", "B", "C", "D", "E"]  # Added "E"

CHARGERS_PER_STATION = {
    "A": 1, "B": 1, "C": 1, "D": 1, "E": 1  # Added "E"
}
```

### 2. Variable Charging Times

**Change:** Different buses or stations may have different charging durations

**How Design Handles It:**
- Add `charging_time_minutes` field to Bus model
- Modify `add_travel_time_constraint()` to use bus-specific charging time
- Update `add_charger_capacity_constraint()` to account for variable durations

```python
# src/models.py
class Bus(BaseModel):
    id: str
    operator: str
    direction: str
    departure_time_minutes: int
    charging_time_minutes: int = 25  # New field with default

# src/constraints.py
def add_travel_time_constraint(model, variables, buses, stations, bus_speed_kmh):
    for bus in buses:
        charging_time = bus.charging_time_minutes  # Use bus-specific time
        for station in stations:
            # ... constraint logic using charging_time
```

### 3. Multiple Charger Types

**Change:** Add fast chargers (10 min) and slow chargers (60 min) at stations

**How Design Handles It:**
- Add `charger_type` field to Station model
- Create separate decision variables for each charger type
- Modify constraints to track charger type assignments
- Update objective to penalize slow charger usage

```python
# src/models.py
class Station(BaseModel):
    id: str
    location_km: int
    fast_chargers: int = 0
    slow_chargers: int = 1

# src/constraints.py
# Create separate variables for each charger type
for bus in buses:
    for station in stations:
        variables['charge_fast'][(bus.id, station)] = model.NewBoolVar(...)
        variables['charge_slow'][(bus.id, station)] = model.NewBoolVar(...)
```

### 4. Real-time Dynamic Updates

**Change:** Buses may be delayed or new buses may be added during operation

**How Design Handles It:**
- Current design supports dynamic bus generation via `generate_dynamic_buses()`
- Can re-run solver with updated scenario to get new schedule
- Consider incremental solving for real-time updates (future enhancement)

```python
# src/utils.py
def generate_dynamic_buses(num_forward, num_reverse, start_time_forward, 
                             start_time_reverse, interval_minutes):
    """Generate buses dynamically based on configuration."""
    buses = []
    for i in range(num_forward):
        buses.append(Bus(
            id=f"bus_forward_{i+1}",
            operator="kpn",
            direction="BK",
            departure_time_minutes=time_to_minutes(start_time_forward) + i * interval_minutes
        ))
    # ... similar for reverse buses
    return buses
```

### 5. Route Variations

**Change:** Add alternative routes (e.g., express route with fewer stops)

**How Design Handles It:**
- Add `route_id` field to Bus model
- Create route definitions in config (segments, stations per route)
- Modify constraint logic to use route-specific data
- Update distance calculations to account for route variations

```python
# src/models.py
class Bus(BaseModel):
    id: str
    operator: str
    direction: str
    departure_time_minutes: int
    route_id: str = "default"  # New field

# config.py
ROUTES = {
    "default": {"segments": [...], "stations": ["A", "B", "C", "D"]},
    "express": {"segments": [...], "stations": ["A", "C"]},  # Skip B
}
```

## How to Change a Weight

The objective function combines three weighted components:
- **Individual weight**: Minimizes wait time for individual buses
- **Operator weight**: Minimizes total wait time per operator (fairness)
- **Overall weight**: Minimizes total system wait time

### Method 1: Via Streamlit UI

Change weights dynamically in the sidebar:

```python
# app.py (Streamlit UI)
individual_weight = st.sidebar.slider("Individual Weight", 0.0, 10.0, 1.0)
operator_weight = st.sidebar.slider("Operator Weight", 0.0, 10.0, 1.0)
overall_weight = st.sidebar.slider("Overall Weight", 0.0, 10.0, 1.0)

weights = {
    "individual": individual_weight,
    "operator": operator_weight,
    "overall": overall_weight
}
```

### Method 2: Via Scenario JSON

Change weights in the scenario file:

```json
{
  "name": "Scenario 1 - Even Spacing",
  "description": "Baseline case with evenly spaced departures",
  "weights": {
    "individual": 2.0,
    "operator": 0.5,
    "overall": 1.0
  },
  "buses": [...]
}
```

### Method 3: Programmatically

Change weights in code:

```python
from src.loader import load_scenario

scenario = load_scenario("data/scenarios/scenario_1_even_spacing.json")

# Modify weights
scenario.weights = {
    "individual": 3.0,  # Prioritize individual wait times
    "operator": 0.1,    # Deprioritize operator fairness
    "overall": 1.0
}

# Run scheduler with new weights
result = scheduler.solve()
```

### Effect of Weight Changes

- **Higher individual weight**: Buses with shorter routes get priority
- **Higher operator weight**: Balances wait times across operators (fairness)
- **Higher overall weight**: Minimizes total system wait time (efficiency)
- **Zero weight**: Disables that component entirely

## Solver Optimization Configuration

The CP-SAT solver has several optimization parameters that can be tuned for performance and solution quality.

### Time Limit

Controls how long the solver searches for an optimal solution:

```python
# config.py
SOLVER_TIME_LIMIT_SECONDS = 60  # Default: 60 seconds
```

**Effects:**
- **Shorter limit (30s)**: Faster results, may be suboptimal
- **Longer limit (120s)**: Better solutions, longer solve time
- **Unlimited (31536000s = 1 year)**: Guarantees optimal solution, may take very long

**How to Change:**

```python
# Method 1: Via config.py
SOLVER_TIME_LIMIT_SECONDS = 120  # Increase to 2 minutes

# Method 2: Via Streamlit UI
unlimited_time = st.sidebar.checkbox("Unlimited Time", value=False)
if unlimited_time:
    max_time = 31536000  # 1 year
else:
    max_time = config.SOLVER_TIME_LIMIT_SECONDS
```

### Search Workers

Controls parallelism in the search algorithm:

```python
# config.py
NUM_SEARCH_WORKERS = 8  # Default: 8 parallel workers
```

**Effects:**
- **More workers (16)**: Faster on multi-core machines, uses more memory
- **Fewer workers (1)**: Slower, deterministic results, less memory
- **Recommended (8)**: Good balance for most systems

**Trade-offs:**
- Parallel workers introduce non-determinism (different results each run)
- Single worker is deterministic but slower
- OR-Tools recommends 8 workers for best performance

```python
# src/scheduler.py
solver = cp_model.CpSolver()
solver.parameters.num_search_workers = config.NUM_SEARCH_WORKERS
```

### Phase 2 Constraint Optimizations (Disabled by Default)

Advanced constraint-level optimizations for very large scenarios (40+ buses):

```python
# config.py
ENABLE_CONSTRAINT_OPTIMIZATIONS = False  # Default: disabled (slows down solver)
TIME_WINDOW_THRESHOLD_MINUTES = 30  # Threshold for time-window filtering
```

**Components:**

1. **Time-Window Decomposition**: Skips ordering constraints when buses arrive too far apart
   - If bus A arrives at 19:00 and bus B at 21:30 (150 min gap), no ordering constraint needed
   - Reduces constraint count significantly

2. **Reachability Filtering**: Removes buses that cannot reach a station
   - Only considers buses that have the station in their route order
   - Reduces variable count

3. **Symmetry Breaking**: Eliminates duplicate solutions
   - Groups buses with identical departure times
   - Enforces lexicographic ordering on charging decisions
   - Reduces search space

**When to Enable:**
- **Small scenarios (<20 buses)**: NOT recommended - slows down solver by 43-62%
- **Medium scenarios (20-40 buses)**: NOT recommended - slows down solver by 43-62%
- **Large scenarios (>40 buses)**: MAY help with filtering, but testing shows mixed results
- **Very large scenarios (50+ buses)**: Only enable if problem size reduction is not feasible

**Note**: Empirical testing shows these optimizations SLOW DOWN the solver by 43-62% for scenarios 1,3,4. They are disabled by default because CP-SAT's built-in constraint propagation is more efficient for this problem structure.

**How to Control:**

```python
# Method 1: Via config.py
ENABLE_CONSTRAINT_OPTIMIZATIONS = True  # Only for very large scenarios
TIME_WINDOW_THRESHOLD_MINUTES = 30

# Method 2: Via Streamlit UI
enable_optimizations = st.sidebar.checkbox("Enable Optimizations", value=False)
```

### Solver-Level Optimizations (Always Enabled)

These solver parameters are always enabled and provide 26-72% improvement for scenarios 1,3,4:

```python
# config.py - Solver-level optimizations
LINEARIZATION_LEVEL = 0  # No LP relaxation - 63-72% improvement for scenarios 1,3,4
ENABLE_HINTS = False  # Disables greedy hints - 26-32% improvement for scenarios 1,3,4
CP_MODEL_PRESOLVE = True  # Enables presolve - 35-60% improvement for scenarios 1,3,4
MAX_NUMBER_OF_CONFLICTS = 500000  # Increased from 100000 - 26-46% improvement for scenarios 1,3,4
```

### Solver Parameters Summary

```python
# config.py - All solver-related parameters
SOLVER_TIME_LIMIT_SECONDS = 60
NUM_SEARCH_WORKERS = 2  # Set to 2 for both local and cloud environments
ENABLE_CONSTRAINT_OPTIMIZATIONS = False  # Phase 2 constraint optimizations (disabled by default)
TIME_WINDOW_THRESHOLD_MINUTES = 30
```

**Recommended Settings:**

| Scenario Size | Time Limit | Workers | Phase 2 Constraint Optimizations |
|--------------|------------|---------|----------------------------------|
| Small (<20) | 30s | 2 | False (slows down solver) |
| Medium (20-40) | 60s | 2 | False (slows down solver) |
| Large (40-100) | 120-300s | 2 | False (slows down solver, use longer time limit instead) |
| Very Large (>100) | 300s+ | 2 | False (use problem size reduction instead) |

### Performance Tuning Tips

1. **For faster solve times**:
   - Solver-level optimizations are already enabled (linearization_level=0, ENABLE_HINTS=False, CP_MODEL_PRESOLVE=True, MAX_NUMBER_OF_CONFLICTS=500000)
   - Reduce time limit to 30-60s for FEASIBLE solutions
   - DO NOT enable Phase 2 constraint optimizations (they slow down the solver by 43-62%)
   - Use 2 workers (consistent across local and cloud)

2. **For better solution quality**:
   - Increase time limit to 120-300s for better FEASIBLE solutions
   - Use unlimited time limit for OPTIMAL solutions (may take 10-60 minutes for large scenarios)
   - Keep solver-level optimizations enabled
   - DO NOT enable Phase 2 constraint optimizations

3. **For very large scenarios (40+ buses)**:
   - Reduce problem size (fewer buses per scheduling window) - this is the ONLY effective approach
   - Increase time limit to 300s+ if problem size cannot be reduced
   - DO NOT enable Phase 2 constraint optimizations (they slow down the solver)
   - Consider heuristic approaches or problem decomposition for 100+ buses (not implemented)

## How to Add a New Rule

The constraint system is modular, making it easy to add new rules. Here's how to add a new constraint:

### Example: Add Maximum Wait Time Constraint

**Requirement:** No bus should wait more than 60 minutes at any station.

### Step 1: Define the Constraint Function

Add a new function in `src/constraints/` (e.g., `src/constraints/range.py` or a new module):

```python
def add_max_wait_time_constraint(
    model: cp_model.CpModel,
    variables: Dict,
    buses: List,
    stations: List[str],
    max_wait_minutes: int = 60
) -> None:
    """
    Add constraint that no bus waits more than max_wait_minutes at any station.
    
    Args:
        model: CP-SAT model
        variables: Dictionary of decision variables
        buses: List of Bus objects
        stations: List of station IDs
        max_wait_minutes: Maximum allowed wait time
    """
    for bus in buses:
        for station in stations:
            wait_time = variables['wait_time'][(bus.id, station)]
            charge_at = variables['charge_at'][(bus.id, station)]
            
            # If bus charges at station, wait_time <= max_wait_minutes
            # This is a conditional constraint: if charge_at=1 then wait_time <= max
            # CP-SAT handles this with implication: charge_at=1 => wait_time <= max
            model.Add(wait_time <= max_wait_minutes).OnlyEnforceIf(charge_at)
```

### Step 2: Add Configuration

Add the new parameter to `config.py`:

```python
# config.py
MAX_WAIT_TIME_MINUTES = 60
```

### Step 3: Integrate into Scheduler

Call the new constraint function in `src/scheduler.py`:

```python
def build_model(self, scenario: Scenario, enable_optimizations: bool = False):
    """Build the CP-SAT model with all constraints."""
    model = cp_model.CpModel()
    variables = {}
    
    # ... create variables ...
    
    # Add all constraints using modular constraint package
    from src.constraints.range import add_range_constraint
    from src.constraints.capacity import add_charger_capacity_constraint
    from src.constraints.route import add_route_order_constraint
    from src.constraints.timing import add_travel_time_constraint
    
    add_range_constraint(model, variables, scenario.buses, stations, 
                        battery_range_km)
    add_charger_capacity_constraint(model, variables, scenario.buses, stations, 
                                    chargers_per_station, enable_optimizations)
    add_route_order_constraint(model, variables, scenario.buses, stations)
    add_travel_time_constraint(model, variables, scenario.buses, stations, 
                              bus_speed_kmh, charging_time_minutes)
    
    # NEW: Add max wait time constraint
    add_max_wait_time_constraint(model, variables, scenario.buses, stations,
                                config.MAX_WAIT_TIME_MINUTES)
    
    # ... add objective ...
    
    return model, variables
```

### Step 4: Add Tests

Add tests in `tests/test_constraints.py` or appropriate test file:

```python
def test_max_wait_time_constraint():
    """Test that max wait time constraint is enforced."""
    model = cp_model.CpModel()
    variables = {'charge_at': {}, 'wait_time': {}}
    
    bus = Bus(id="bus-1", operator="kpn", direction="BK", departure_time_minutes=1140)
    stations = ['A', 'B', 'C', 'D']
    
    # Create variables
    for station in stations:
        variables['charge_at'][(bus.id, station)] = model.NewBoolVar(f"charge_{bus.id}_{station}")
        variables['wait_time'][(bus.id, station)] = model.NewIntVar(0, 1440, f"wait_{bus.id}_{station}")
    
    # Add constraint
    add_max_wait_time_constraint(model, variables, [bus], stations, max_wait_minutes=60)
    
    # Function should complete without error
    assert len(model.Constraints()) > 0
```

### Step 5: Document the Rule

Add documentation to `README.md`:

```markdown
### Constraints

The scheduler enforces the following constraints:

- **Range Constraint**: Buses must have sufficient battery range
- **Charger Capacity**: No station can exceed its charger capacity
- **Route Order**: Buses must charge in route order
- **Travel Time**: Charging must account for travel time
- **Max Wait Time**: No bus waits more than 60 minutes (configurable)
```

### Example: Add New Objective Component

**Requirement:** Penalize buses that charge at multiple stations (encourage single charge).

```python
# src/objectives.py
def build_objective(model, variables, buses, stations, weights):
    # ... existing objective logic ...
    
    # NEW: Add penalty for multiple charges
    multi_charge_penalty = model.NewIntVar(0, 100000, "multi_charge_penalty")
    multi_charge_terms = []
    
    for bus in buses:
        # Count charges for this bus
        bus_charges = model.NewIntVar(0, 10, f"bus_charges_{bus.id}")
        charge_vars = [variables['charge_at'][(bus.id, station)] for station in stations]
        model.Add(bus_charges == sum(charge_vars))
        
        # If charges > 1, add penalty
        is_multi_charge = model.NewBoolVar(f"is_multi_{bus.id}")
        model.Add(is_multi_charge == 1).OnlyEnforceIf(bus_charges > 1)
        model.Add(is_multi_charge == 0).OnlyEnforceIf(bus_charges <= 1)
        multi_charge_terms.append(is_multi_charge)
    
    model.AddMultiplicationEquality(multi_charge_penalty, [sum(multi_charge_terms), 100])
    
    # Add to weighted objective
    model.Add(weighted_objective == scaled_ind + scaled_op + scaled_ov + scaled_charging + multi_charge_penalty)
    
    return weighted_objective
```

### Performance Optimizations

The scheduler includes several optimizations to improve solve time and solution quality:

#### Modular Variable Management
- **scheduler_variables.py**: Centralized variable creation via `VariableManager` class
- Separates variable creation logic from constraint building
- Enables easier debugging and maintenance of variable definitions

#### Modular Solution Extraction
- **scheduler_solution.py**: Solution parsing via `SolutionExtractor` class
- Extracts charging plans from CP-SAT solver response
- Converts solver variables into human-readable charging events

#### Constraint Modularity
- **constraints/ package**: Separate modules for each constraint type
  - `range.py`: Battery range constraints
  - `capacity.py`: Charger capacity constraints with symmetry breaking
  - `route.py`: Route order constraints
  - `timing.py`: Timing constraints (duration, travel, arrival)
- Enables easy addition of new constraints
- Improves code organization and maintainability

#### Utility Functions
- **utils/ package**: Helper functions for common operations
  - `route.py`: Route and distance calculations
  - `time.py`: Time conversion and travel time calculations
  - `bus_generation.py`: Dynamic bus generation for testing
- Reusable across different parts of the system

### Solver Statistics

The UI displays detailed solver metrics in the "Solver Performance Analytics" section (main UI area, accordion format):

- **Solver Status**: OPTIMAL (found best solution) or FEASIBLE (found valid solution within time limit)
- **Optimal Solution %**: Derived from optimality gap (100% for OPTIMAL)
- **Solve Time**: Time taken by the CP-SAT solver in seconds
- **Optimality Gap**: Percentage difference between best solution found and theoretical optimum (0% for OPTIMAL)
- **Variables Count**: Number of decision variables in the CP-SAT model
- **Constraints Count**: Number of constraints in the CP-SAT model
- **Branches Explored**: Number of search tree branches explored during solving
- **Conflicts Resolved**: Number of constraint conflicts resolved by the solver
- **Solver Efficiency Metrics**: Variables/second, constraints/second, branches/second

These metrics help diagnose solver performance and understand solution quality.

### Physical Assumptions

1. **Battery Range**: All buses have the same battery range (240 km) when fully charged
2. **Charging Speed**: All chargers have the same charging rate (25 minutes for full charge)
3. **Bus Speed**: All buses travel at the same average speed (60 km/h)
4. **Route Topology**: The route is fixed (Bengaluru to Kochi via A, B, C, D stations)
5. **No Battery Degradation**: Battery range is constant regardless of age or usage

### Operational Assumptions

1. **Deterministic Travel Time**: Travel time is calculated based on distance and speed, with no traffic delays
2. **No Breakdowns**: Buses and chargers are 100% reliable
3. **Fixed Departure Times**: Bus departure times are known in advance and don't change
4. **No Pre-emption**: Charging cannot be interrupted once started
5. **Instant Queueing**: Buses can queue at stations with no overhead

### Solver Assumptions

1. **Time Limit**: The solver has a 60-second time limit for production use
2. **Parallel Search**: Uses CP-SAT default parallel search (adaptive based on problem size)
3. **Optimality Goal**: Aims for optimal solution, accepts feasible if time limit reached
4. **Deterministic with Fixed Seed**: With fixed random seed, results are reproducible (not currently used)
5. **Integer Precision**: Time is represented in minutes (integer arithmetic)

### Data Assumptions

1. **Unique Bus IDs**: All bus IDs in a scenario must be unique
2. **Valid Directions**: Only 'BK' (Bengaluru→Kochi) and 'KB' (Kochi→Bengaluru) are supported
3. **Valid Operators**: Only 'kpn', 'freshbus', 'flixbus' are supported (configurable)
4. **Non-negative Weights**: All optimization weights must be non-negative
5. **Complete Scenarios**: Scenario files must contain all required fields

### Performance Assumptions

1. **Scalability**: The solver can handle up to 40 buses with current configuration (scenarios 2 and 5 with 20 buses still hit 60s time limit)
2. **Memory Usage**: Memory usage scales linearly with number of buses and stations
3. **Solve Time**: Solve time increases exponentially with problem size
4. **Solver-Level Optimizations**: Provide 26-72% improvement for scenarios 1,3,4 but no improvement for scenarios 2,5
5. **Phase 2 Constraint Optimizations**: Disabled by default (slows down solver by 43-62% for scenarios 1,3,4)
6. **Problem Size Reduction**: Only effective approach for large scenarios with high contention (scenarios 2,5)
7. **Caching**: Streamlit caching reduces re-computation for unchanged inputs

### Future Considerations

These assumptions may need revision for:
- Real-world deployment with traffic variability
- Different bus types with different ranges/speeds
- Dynamic pricing or priority-based scheduling
- Integration with real-time bus tracking systems
- Multi-objective optimization with conflicting goals
