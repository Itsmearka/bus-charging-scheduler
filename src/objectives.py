"""
Objective functions for Bus Charging Scheduler.
Builds weighted objective for CP-SAT optimization.
"""

from typing import Dict, List
from ortools.sat.python import cp_model


def build_objective(
    model: cp_model.CpModel,
    variables: Dict,
    buses: List,
    stations: List[str],
    weights: Dict[str, float]
) -> cp_model.IntVar:
    """
    Build the weighted objective function combining individual, operator, and overall penalties.
    
    Args:
        model: CP-SAT model
        variables: Dictionary of decision variables
        buses: List of Bus objects
        stations: List of station IDs
        weights: Dictionary of optimization weights (individual, operator, overall)
        
    Returns:
        CP-SAT variable representing the objective to minimize
    """
    # Calculate individual penalty: sum of all wait times
    individual_penalty = model.NewIntVar(0, 100000, "individual_penalty")
    wait_terms = []
    for bus in buses:
        for station in stations:
            wait_time = variables['wait_time'][(bus.id, station)]
            wait_terms.append(wait_time)
    
    # Sum all wait times
    model.Add(individual_penalty == sum(wait_terms))
    
    # Calculate operator penalty: sum of wait times per operator, weighted
    # Group buses by operator
    operators = {}
    for bus in buses:
        if bus.operator not in operators:
            operators[bus.operator] = []
        operators[bus.operator].append(bus)
    
    operator_penalty = model.NewIntVar(0, 100000, "operator_penalty")
    operator_terms = []
    for operator, operator_buses in operators.items():
        operator_wait = model.NewIntVar(0, 100000, f"operator_wait_{operator}")
        operator_wait_terms = []
        for bus in operator_buses:
            for station in stations:
                wait_time = variables['wait_time'][(bus.id, station)]
                operator_wait_terms.append(wait_time)
        model.Add(operator_wait == sum(operator_wait_terms))
        operator_terms.append(operator_wait)
    
    # Sum operator wait times
    model.Add(operator_penalty == sum(operator_terms))
    
    # Calculate overall penalty: same as individual (total system time)
    # In this implementation, overall penalty is the same as individual penalty
    # but could be extended to include other factors like arrival time variance
    overall_penalty = individual_penalty
    
    # Calculate charging stops penalty: penalize excessive charging
    # Each charging stop adds 25 minutes, so we penalize total charging time
    # This encourages the solver to minimize the number of charges
    charging_penalty = model.NewIntVar(0, 100000, "charging_penalty")
    charge_terms = []
    for bus in buses:
        for station in stations:
            charge_var = variables['charge_at'][(bus.id, station)]
            charge_terms.append(charge_var)
    
    # Total number of charges across all buses
    total_charges = model.NewIntVar(0, 1000, "total_charges")
    model.Add(total_charges == sum(charge_terms))
    
    # Penalty: 25 minutes per charge (equivalent to charging time)
    # This makes the solver prefer fewer charges when wait times are equal
    model.AddMultiplicationEquality(charging_penalty, [total_charges, 25])
    
    # Combine weighted objectives using integer scaling
    # Scale weights to integers (multiply by 100)
    w_ind = int(weights['individual'] * 100)
    w_op = int(weights['operator'] * 100)
    w_ov = int(weights['overall'] * 100)
    
    weighted_objective = model.NewIntVar(0, 10000000, "weighted_objective")
    
    # Create scaled penalty terms
    scaled_ind = model.NewIntVar(0, 10000000, "scaled_individual")
    scaled_op = model.NewIntVar(0, 10000000, "scaled_operator")
    scaled_ov = model.NewIntVar(0, 10000000, "scaled_overall")
    scaled_charging = model.NewIntVar(0, 10000000, "scaled_charging")
    
    model.AddMultiplicationEquality(scaled_ind, [individual_penalty, w_ind])
    model.AddMultiplicationEquality(scaled_op, [operator_penalty, w_op])
    model.AddMultiplicationEquality(scaled_ov, [overall_penalty, w_ov])
    # Weight charging penalty same as overall (multiply by 100 for scaling)
    model.AddMultiplicationEquality(scaled_charging, [charging_penalty, 100])
    
    model.Add(weighted_objective == scaled_ind + scaled_op + scaled_ov + scaled_charging)
    
    return weighted_objective


def add_minimize_max_wait_objective(
    model: cp_model.CpModel,
    variables: Dict,
    buses: List,
    stations: List[str]
) -> cp_model.IntVar:
    """
    Add objective to minimize the maximum wait time across all buses.
    This is a fairness-focused objective.
    
    Args:
        model: CP-SAT model
        variables: Dictionary of decision variables
        buses: List of Bus objects
        stations: List of station IDs
        
    Returns:
        CP-SAT variable representing the maximum wait time
    """
    # Create a variable for maximum wait time
    max_wait = model.NewIntVar(0, 100000, "max_wait")
    
    # Add constraints that max_wait >= each individual wait time
    for bus in buses:
        for station in stations:
            wait_time = variables['wait_time'][(bus.id, station)]
            model.Add(max_wait >= wait_time)
    
    return max_wait


def add_minimize_arrival_time_variance_objective(
    model: cp_model.CpModel,
    variables: Dict,
    buses: List
) -> cp_model.IntVar:
    """
    Add objective to minimize variance in arrival times.
    This ensures buses arrive more evenly spaced.
    
    Args:
        model: CP-SAT model
        variables: Dictionary of decision variables
        buses: List of Bus objects
        
    Returns:
        CP-SAT variable representing arrival time variance
    """
    # Calculate mean arrival time
    arrival_times = [variables['arrival_time_final'][bus.id] for bus in buses]
    mean_arrival = model.NewIntVar(0, 100000, "mean_arrival")
    model.Add(mean_arrival == sum(arrival_times) // len(arrival_times))
    
    # Calculate variance (simplified as sum of absolute deviations)
    variance = model.NewIntVar(0, 100000, "arrival_variance")
    deviations = []
    for bus in buses:
        deviation = model.NewIntVar(0, 100000, f"deviation_{bus.id}")
        arrival = variables['arrival_time_final'][bus.id]
        # deviation = |arrival - mean|
        model.Add(deviation >= arrival - mean_arrival)
        model.Add(deviation >= mean_arrival - arrival)
        deviations.append(deviation)
    
    model.Add(variance == sum(deviations))
    
    return variance
