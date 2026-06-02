"""
Bus Charging Scheduler - Streamlit UI
Interactive web application for visualizing and tuning charging schedules.
"""

import streamlit as st
import time
from src.loader import load_scenario
from src.scheduler import BusChargingScheduler
from ui.styles import apply_custom_styles


# Page configuration with native dark mode support
st.set_page_config(
    page_title="Bus Charging Scheduler",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
)

# Apply custom styles
apply_custom_styles()


@st.cache_data
def load_scenario_cached(scenario_path):
    """Load scenario with caching."""
    return load_scenario(scenario_path)


@st.cache_data
def run_scheduler(_scenario_input, weights, enable_optimizations, unlimited_time=False, _cache_key=None):
    """
    Run scheduler with caching based on scenario, weights, and optimization flag.
    
    Args:
        _scenario_input: Scenario object or file path
        weights: Dictionary of optimization weights
        enable_optimizations: Whether to use Phase 2 optimizations
        unlimited_time: Whether to disable solver time limit
        _cache_key: Cache key for Streamlit caching
    
    Returns:
        tuple: (result, scenario)
    """
    # Load scenario if file path provided, otherwise use provided scenario object
    if isinstance(_scenario_input, str):
        scenario = load_scenario_cached(_scenario_input)
    else:
        scenario = _scenario_input
    
    # Update weights
    scenario.weights = weights
    
    # Run scheduler
    scheduler = BusChargingScheduler(scenario, enable_optimizations=enable_optimizations, unlimited_time=unlimited_time)
    result = scheduler.solve()
    
    return result, scenario


def run_scheduler_uncached(scenario, weights, enable_optimizations, unlimited_time=False):
    """
    Run scheduler without caching (for dynamic scenarios).
    
    Args:
        scenario: Scenario object
        weights: Dictionary of optimization weights
        enable_optimizations: Whether to use Phase 2 optimizations
        unlimited_time: Whether to disable solver time limit
    
    Returns:
        tuple: (result, scenario)
    """
    # Update weights
    scenario.weights = weights
    
    # Run scheduler
    scheduler = BusChargingScheduler(scenario, enable_optimizations=enable_optimizations, unlimited_time=unlimited_time)
    result = scheduler.solve()
    
    return result, scenario


def show_loading_animation():
    """Display a visual loading animation."""
    animation = st.empty()
    for i in range(3):
        animation.markdown("Loading" + "." * (i + 1))
        time.sleep(0.3)
    animation.empty()


def main():
    """
    Main application function.
    Orchestrates the UI, sidebar, and solver execution.
    """
    st.title("Bus Charging Scheduler")
    st.markdown("Electric bus charging optimization using CP-SAT constraint programming")
    
    # Render sidebar and get configuration
    from ui.sidebar import render_sidebar
    from ui.results import render_results
    import config
    
    scenario, weights, enable_optimizations, unlimited_time, use_dynamic, run_clicked = render_sidebar()
    
    # Create cache key for current configuration
    if use_dynamic:
        cache_key = f"dynamic_{weights['individual']}_{weights['operator']}_{weights['overall']}_{enable_optimizations}_{unlimited_time}"
    else:
        from src.loader import list_available_scenarios
        scenario_files = list_available_scenarios()
        selected_scenario_file = scenario_files[0]  # Will be properly set by sidebar
        cache_key = f"{selected_scenario_file}_{weights['individual']}_{weights['operator']}_{weights['overall']}_{enable_optimizations}_{unlimited_time}"
    
    # Display estimated solve time
    if unlimited_time:
        st.info("Running with unlimited time - may take significantly longer for optimal solution")
    else:
        st.info("Guaranteed feasible solution within time limit. Enable unlimited time for optimal solution on larger datasets.")
    
    # Show configuration summary at the top (always display current configuration)
    with st.expander("Configuration Details", expanded=False):
        col1, col2, col3 = st.columns(3)
        col1.metric("Buses", len(scenario.buses))
        col2.metric("Stations", len(config.STATIONS))
        col3.metric("Optimizations", "Enabled" if enable_optimizations else "Disabled")
        
        st.markdown(f"""
        **Weights:**
        - Individual: {weights['individual']}
        - Operator: {weights['operator']}
        - Overall: {weights['overall']}
        
        **Time Limit:** {config.SOLVER_TIME_LIMIT_SECONDS}s
        """)
    
    # Only run solver when Run button is clicked
    if not run_clicked and 'solver_result' not in st.session_state:
        st.info("👆 Click the 'Run Scheduler' button in the sidebar to start the optimization")
        st.stop()
    
    # Run scheduler with progress indicators (only when button clicked)
    if run_clicked:
        try:
            # Set solver running state
            st.session_state['solver_running'] = True
            
            # Check if we have cached results for this configuration
            if 'solver_cache' in st.session_state and cache_key in st.session_state['solver_cache']:
                result = st.session_state['solver_cache'][cache_key]['result']
                scenario = st.session_state['solver_cache'][cache_key]['scenario']
                st.success("Using cached solution from previous run")
            else:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Show loading animation
                show_loading_animation()
                
                status_text.text("Initializing solver...")
                progress_bar.progress(10)
                
                status_text.text("Building constraints and variables...")
                progress_bar.progress(30)
                
                status_text.text("Solving optimization problem using CP-SAT...")
                progress_bar.progress(50)
                
                # Run solver with spinner
                with st.spinner("Solving scheduling problem using CP-SAT solver..."):
                    if use_dynamic:
                        result, scenario = run_scheduler_uncached(scenario, weights, enable_optimizations, unlimited_time)
                    else:
                        from src.loader import list_available_scenarios
                        scenario_files = list_available_scenarios()
                        # Get the actual selected scenario file from session state or sidebar
                        if 'selected_scenario_file' in st.session_state:
                            selected_scenario_file = st.session_state['selected_scenario_file']
                        else:
                            selected_scenario_file = scenario_files[0]
                        result, scenario = run_scheduler(selected_scenario_file, weights, enable_optimizations, unlimited_time)
                
                progress_bar.progress(100)
                status_text.text("Solution found!")
                
                # Clear progress indicators
                progress_bar.empty()
                status_text.empty()
                
                # Cache the results
                if 'solver_cache' not in st.session_state:
                    st.session_state['solver_cache'] = {}
                st.session_state['solver_cache'][cache_key] = {
                    'result': result,
                    'scenario': scenario
                }
            
            # Store result in session state for persistence
            st.session_state['solver_result'] = result
            st.session_state['solver_scenario'] = scenario
            st.session_state['solver_weights'] = weights
            
            # Set solver running state to False
            st.session_state['solver_running'] = False
            
            # Display solve status
            if result.solver_status == "OPTIMAL":
                st.success(f"Solver found OPTIMAL solution in {result.solve_time_seconds:.2f} seconds")
            elif result.solver_status == "FEASIBLE":
                st.warning(f"Solver found FEASIBLE solution in {result.solve_time_seconds:.2f} seconds (time limit reached)")
            else:
                st.error(f"Solver status: {result.solver_status}")
            
            # Display optimization status
            if enable_optimizations:
                st.info("Optimizations enabled")
        
        except Exception as e:
            st.session_state['solver_running'] = False
            st.error(f"Error running scheduler: {e}")
            st.stop()
    
    # Load results from session state if they exist (for display after button click)
    if 'solver_result' in st.session_state:
        result = st.session_state['solver_result']
        scenario = st.session_state['solver_scenario']
        weights = st.session_state['solver_weights']
    
    # Only show tabs if solver is not running and we have results
    if not st.session_state.get('solver_running', False) and 'solver_result' in st.session_state:
        # Render results tabs
        render_results(result, scenario, weights)


if __name__ == "__main__":
    main()
