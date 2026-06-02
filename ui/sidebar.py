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
    st.sidebar.header("Configuration")
    
    # Add manual Run button at the top
    run_clicked = st.sidebar.button("🚀 Run Scheduler", type="primary", use_container_width=True)
    
    # Separator after Run button
    st.sidebar.markdown("---")
    
    # Show interesting fact carousel in sidebar
    from ui.carousels import show_fact_carousel
    show_fact_carousel()
    
    # Show architectural decisions carousel in sidebar
    from ui.carousels import show_arch_decisions_carousel
    show_arch_decisions_carousel()
    
    # Separator between carousels and scenario selector
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
    enable_optimizations = st.sidebar.checkbox(
        "Enable Optimizations",
        value=False,
        help="Enable time-window decomposition and station filtering for larger scenarios"
    )
    
    # Remove time limit toggle
    unlimited_time = st.sidebar.checkbox(
        "Remove Time Limit (Run Until Optimal)",
        value=False,
        help="Disable solver time limit to find guaranteed optimal solution (may take very long)"
    )
    
    # Separator between optimizations and dynamic bus configuration
    st.sidebar.markdown("---")
    
    # Dynamic Bus Configuration Section
    st.sidebar.subheader("Dynamic Bus Configuration")
    
    use_dynamic = st.sidebar.checkbox("Use Dynamic Bus Generation", value=False)
    
    scenario, weights = None, None
    
    if use_dynamic:
        scenario, weights = render_dynamic_bus_config()
    else:
        scenario, weights = render_scenario_config(selected_scenario_file, use_dynamic)
    
    return scenario, weights, enable_optimizations, unlimited_time, use_dynamic, run_clicked


@st.cache_data
def load_scenario_cached(scenario_path):
    """Load scenario with caching."""
    return load_scenario(scenario_path)


def render_dynamic_bus_config():
    """
    Render dynamic bus configuration UI.
    
    Returns:
        tuple: (scenario, weights_dict)
    """
    col1, col2 = st.sidebar.columns(2)
    with col1:
        num_forward = st.sidebar.number_input(
            "Forward Buses",
            min_value=1,
            max_value=50,
            value=10,
            step=1
        )
    with col2:
        num_reverse = st.sidebar.number_input(
            "Reverse Buses",
            min_value=1,
            max_value=50,
            value=10,
            step=1
        )
    
    col3, col4 = st.sidebar.columns(2)
    with col3:
        start_time_forward = st.sidebar.time_input(
            "Forward Start Time",
            value=datetime.strptime("19:00", "%H:%M").time()
        )
    with col4:
        start_time_reverse = st.sidebar.time_input(
            "Reverse Start Time",
            value=datetime.strptime("19:00", "%H:%M").time()
        )
    
    interval_minutes = st.sidebar.slider(
        "Departure Interval (min)",
        min_value=5,
        max_value=60,
        value=15,
        step=5
    )
    
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
    
    # Generate dynamic scenario
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
        name=f"Dynamic - {num_forward}F/{num_reverse}R",
        description=f"Dynamically generated: {num_forward} forward, {num_reverse} reverse buses",
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
    
    # Display scenario metadata (only if not dynamic)
    if not use_dynamic:
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
