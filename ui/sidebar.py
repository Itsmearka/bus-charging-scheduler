"""
UI Sidebar Module
Sidebar components for configuration and scenario selection.
"""

import streamlit as st
from datetime import datetime
from src.loader import load_scenario, list_available_scenarios
from src.utils.bus_generation import generate_dynamic_buses


def render_sidebar():
    """
    Render the sidebar with configuration options.
    
    Returns:
        tuple: (scenario, weights_dict, enable_optimizations, unlimited_time, use_dynamic, run_clicked)
    """
    
    
    # Add separate Run and Clear Cache buttons side by side
    col_run, col_clear = st.sidebar.columns([3, 1])
    with col_run:
        run_clicked = st.sidebar.button("Run solver", type="primary", use_container_width=True)
    with col_clear:
        clear_cache_clicked = st.sidebar.button("Clear cache", help="Clear all caches", use_container_width=True)
    
    # Clear cache if button clicked
    if clear_cache_clicked:
        st.cache_data.clear()
        # Preserve UI state before clearing solver results
        # Save UI state keys (widget keys, not cache keys)
        ui_state_to_preserve = {
            'enable_optimizations_checkbox': st.session_state.get('enable_optimizations_checkbox', False),
            'unlimited_time_checkbox': st.session_state.get('unlimited_time_checkbox', False),
            'use_dynamic_checkbox': st.session_state.get('use_dynamic_checkbox', False),
            'num_forward_input': st.session_state.get('num_forward_input', 10),
            'num_reverse_input': st.session_state.get('num_reverse_input', 10),
            'start_time_forward_input': st.session_state.get('start_time_forward_input', datetime.strptime("19:00", "%H:%M").time()),
            'start_time_reverse_input': st.session_state.get('start_time_reverse_input', datetime.strptime("19:00", "%H:%M").time()),
            'interval_minutes_input': st.session_state.get('interval_minutes_input', 15),
        }
        
        # Clear session state cache (solver results only)
        if 'solver_cache' in st.session_state:
            del st.session_state['solver_cache']
        if 'solver_result' in st.session_state:
            del st.session_state['solver_result']
        if 'solver_scenario' in st.session_state:
            del st.session_state['solver_scenario']
        if 'solver_weights' in st.session_state:
            del st.session_state['solver_weights']
        if 'last_cache_key' in st.session_state:
            del st.session_state['last_cache_key']
        
        # Restore UI state
        for key, value in ui_state_to_preserve.items():
            st.session_state[key] = value
        
        st.sidebar.success("Cache cleared!")
        st.rerun()
    
    # Separator after buttons
    st.sidebar.markdown("---")
    
    # Get available scenarios
    scenario_files = list_available_scenarios()
    
    # Extract scenario names for dropdown
    scenario_names = []
    for scenario_file in scenario_files:
        try:
            scenario = load_scenario_cached(scenario_file)
            scenario_names.append(scenario.name)
        except:
            scenario_names.append(scenario_file)
    
    

    # Scenario selector
    selected_scenario_index = st.sidebar.selectbox(
        "Select Scenario",
        range(len(scenario_names)),
        format_func=lambda i: scenario_names[i]
    )
    
    selected_scenario_file = scenario_files[selected_scenario_index]
    
    # Store selected scenario file in session state for app.py to use
    st.session_state['selected_scenario_file'] = selected_scenario_file
    
    # Separator between scenario selector and optimizations
    st.sidebar.markdown("---")
    
    # Optimizations toggle
    if 'enable_optimizations_checkbox' not in st.session_state:
        st.session_state['enable_optimizations_checkbox'] = False
    enable_optimizations = st.sidebar.checkbox(
        "Enable Optimizations",
        key='enable_optimizations_checkbox',
        help="Enable time-window decomposition, reachability filtering, and symmetry breaking (may slow down solver for small scenarios)"
    )
    # Update session state for cache key generation
    st.session_state['enable_optimizations'] = enable_optimizations
    
    # Remove time limit toggle
    if 'unlimited_time_checkbox' not in st.session_state:
        st.session_state['unlimited_time_checkbox'] = False
    unlimited_time = st.sidebar.checkbox(
        "Remove Time Limit (Run Until Optimal)",
        key='unlimited_time_checkbox',
        help="Disable solver time limit to find guaranteed optimal solution (may take very long)"
    )
    # Update session state for cache key generation
    st.session_state['unlimited_time'] = unlimited_time
    
    # Separator between optimizations and dynamic bus configuration
    st.sidebar.markdown("---")
    
    # Dynamic Bus Configuration Section
    st.sidebar.subheader("Dynamic Bus Configuration")
    
    if 'use_dynamic_checkbox' not in st.session_state:
        st.session_state['use_dynamic_checkbox'] = False
    use_dynamic = st.sidebar.checkbox("Use Dynamic Bus Generation", key='use_dynamic_checkbox')
    # Update session state for cache key generation
    st.session_state['use_dynamic'] = use_dynamic
    
    scenario, weights = None, None
    
    if use_dynamic:
        scenario, weights = render_dynamic_bus_config(selected_scenario_file)
    else:
        scenario, weights = render_scenario_config(selected_scenario_file, use_dynamic)
    
    return scenario, weights, enable_optimizations, unlimited_time, use_dynamic, run_clicked


@st.cache_data
def load_scenario_cached(scenario_path):
    """Load scenario with caching."""
    return load_scenario(scenario_path)


def render_dynamic_bus_config(selected_scenario_file):
    """
    Render dynamic bus configuration UI.
    
    Args:
        selected_scenario_file: Base scenario file to use for dynamic generation
    
    Returns:
        tuple: (scenario, weights_dict)
    """
    col1, col2 = st.sidebar.columns(2)
    with col1:
        st.sidebar.number_input(
            "Forward Buses",
            min_value=1,
            max_value=50,
            value=10,
            step=1,
            key='num_forward_input'
        )
    with col2:
        st.sidebar.number_input(
            "Reverse Buses",
            min_value=1,
            max_value=50,
            value=10,
            step=1,
            key='num_reverse_input'
        )
    
    col3, col4 = st.sidebar.columns(2)
    with col3:
        st.sidebar.time_input(
            "Forward Start Time",
            value=datetime.strptime("19:00", "%H:%M").time(),
            key='start_time_forward_input'
        )
    with col4:
        st.sidebar.time_input(
            "Reverse Start Time",
            value=datetime.strptime("19:00", "%H:%M").time(),
            key='start_time_reverse_input'
        )
    
    st.sidebar.slider(
        "Departure Interval (min)",
        min_value=5,
        max_value=60,
        value=15,
        step=5,
        key='interval_minutes_input'
    )
    
    # Read values from session state after widgets are rendered
    num_forward = st.session_state['num_forward_input']
    num_reverse = st.session_state['num_reverse_input']
    start_time_forward = st.session_state['start_time_forward_input']
    start_time_reverse = st.session_state['start_time_reverse_input']
    interval_minutes = st.session_state['interval_minutes_input']
    
    # Update session state for cache key generation
    st.session_state['num_forward'] = num_forward
    st.session_state['num_reverse'] = num_reverse
    st.session_state['start_time_forward'] = start_time_forward.strftime("%H:%M")
    st.session_state['start_time_reverse'] = start_time_reverse.strftime("%H:%M")
    st.session_state['interval_minutes'] = interval_minutes
    
    # Separator before weight tuning
    st.sidebar.markdown("---")
    
    # Weight tuning section for dynamic scenarios
    st.sidebar.subheader("Optimization Weights")
    
    individual_weight = st.sidebar.slider(
        "Individual Weight",
        min_value=0.0,
        max_value=5.0,
        value=1.0,
        step=0.1,
        help="Minimize wait time for individual buses"
    )
    
    operator_weight = st.sidebar.slider(
        "Operator Weight",
        min_value=0.0,
        max_value=5.0,
        value=1.0,
        step=0.1,
        help="Minimize delays across operator fleets"
    )
    
    overall_weight = st.sidebar.slider(
        "Overall Weight",
        min_value=0.0,
        max_value=5.0,
        value=1.0,
        step=0.1,
        help="Minimize total system time"
    )
    
    # Load base scenario to get its name
    base_scenario = load_scenario_cached(selected_scenario_file)
    
    # Generate dynamic scenario using values read from session state
    dynamic_buses = generate_dynamic_buses(
        num_forward=num_forward,
        num_reverse=num_reverse,
        start_time_forward=start_time_forward.strftime("%H:%M"),
        start_time_reverse=start_time_reverse.strftime("%H:%M"),
        interval_minutes=interval_minutes
    )
    
    # Create in-memory scenario with user-adjusted weights
    from src.models import Scenario
    scenario = Scenario(
        name=f"{base_scenario.name} (Dynamic {num_forward}F/{num_reverse}R)",
        description=f"Dynamic variant of {base_scenario.name}: {num_forward} forward, {num_reverse} reverse buses",
        weights={'individual': individual_weight, 'operator': operator_weight, 'overall': overall_weight},
        buses=dynamic_buses
    )
    
    # Use user-adjusted weights from sliders
    weights = {
        'individual': individual_weight,
        'operator': operator_weight,
        'overall': overall_weight
    }
    
    return scenario, weights


def render_scenario_config(scenario_file, use_dynamic):
    """
    Render scenario configuration UI.
    
    Args:
        scenario_file: Path to scenario file
        use_dynamic: Whether dynamic generation is enabled
    
    Returns:
        tuple: (scenario, weights_dict)
    """
    # Load selected scenario
    scenario = load_scenario_cached(scenario_file)
    
    # Separator between dynamic bus configuration and scenario details
    st.sidebar.markdown("---")
    
    # Display scenario metadata (always visible)
    st.sidebar.subheader("Scenario Details")
    st.sidebar.write(f"**Name:** {scenario.name}")
    st.sidebar.write(f"**Buses:** {len(scenario.buses)}")
    st.sidebar.write(f"**Description:** {scenario.description}")
    
    # Separator before weight tuning
    st.sidebar.markdown("---")
    
    # Weight tuning
    st.sidebar.subheader("Optimization Weights")
    
    individual_weight = st.sidebar.slider(
        "Individual Weight",
        min_value=0.0,
        max_value=5.0,
        value=scenario.weights.get('individual', 1.0),
        step=0.1,
        help="Minimize wait time for individual buses"
    )
    
    operator_weight = st.sidebar.slider(
        "Operator Weight",
        min_value=0.0,
        max_value=5.0,
        value=scenario.weights.get('operator', 1.0),
        step=0.1,
        help="Minimize delays across operator fleets"
    )
    
    overall_weight = st.sidebar.slider(
        "Overall Weight",
        min_value=0.0,
        max_value=5.0,
        value=scenario.weights.get('overall', 1.0),
        step=0.1,
        help="Minimize total system time"
    )
    
    # Combine weights into dictionary for scheduler
    weights = {
        'individual': individual_weight,
        'operator': operator_weight,
        'overall': overall_weight
    }
    
    return scenario, weights
