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





def run_scheduler(scenario_input, weights, enable_optimizations, unlimited_time=False, cache_key=None):

    """

    Run scheduler with manual caching based on cache key.

    

    Args:

        scenario_input: Scenario object or file path

        weights: Dictionary of optimization weights

        enable_optimizations: Whether to use Phase 2 optimizations

        unlimited_time: Whether to disable solver time limit

        cache_key: Cache key for manual caching

    

    Returns:

        tuple: (result, scenario)

    """

    # Check manual cache first

    if 'solver_cache' not in st.session_state:

        st.session_state['solver_cache'] = {}

    

    if cache_key and cache_key in st.session_state['solver_cache']:

        st.success("Using cached solution from previous run")

        return st.session_state['solver_cache'][cache_key]['result'], st.session_state['solver_cache'][cache_key]['scenario']

    

    # Load scenario if file path provided, otherwise use provided scenario object

    if isinstance(scenario_input, str):

        scenario = load_scenario_cached(scenario_input)

    else:

        scenario = scenario_input

    

    # Update weights

    scenario.weights = weights

    

    # Run scheduler

    scheduler = BusChargingScheduler(scenario, enable_optimizations=enable_optimizations, unlimited_time=unlimited_time)

    result = scheduler.solve()

    

    # Cache the result

    if cache_key:

        st.session_state['solver_cache'][cache_key] = {

            'result': result,

            'scenario': scenario

        }

    

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



    # Create cache key for current configuration (moved before config details for display)

    if use_dynamic:

        # For dynamic scenarios, include base scenario and bus generation parameters in cache key

        # Use widget keys directly to ensure cache key reflects current widget values

        selected_scenario_file = st.session_state.get('selected_scenario_file', 'scenario_1_even_spacing.json')

        num_forward = st.session_state.get('num_forward_input', 10)

        num_reverse = st.session_state.get('num_reverse_input', 10)

        start_time_forward = st.session_state.get('start_time_forward_input')

        start_time_reverse = st.session_state.get('start_time_reverse_input')

        interval_minutes = st.session_state.get('interval_minutes_input', 15)

        # Format time objects to strings for cache key
        if start_time_forward:
            start_time_forward_str = start_time_forward.strftime("%H:%M") if hasattr(start_time_forward, 'strftime') else str(start_time_forward)
        else:
            start_time_forward_str = "19:00"

        if start_time_reverse:
            start_time_reverse_str = start_time_reverse.strftime("%H:%M") if hasattr(start_time_reverse, 'strftime') else str(start_time_reverse)
        else:
            start_time_reverse_str = "19:00"

        cache_key = f"dynamic_{selected_scenario_file}_{num_forward}_{num_reverse}_{start_time_forward_str}_{start_time_reverse_str}_{interval_minutes}_{weights['individual']}_{weights['operator']}_{weights['overall']}_{enable_optimizations}_{unlimited_time}"

    else:

        # Get selected scenario from session state (set by sidebar)

        selected_scenario_file = st.session_state.get('selected_scenario_file', 'scenario_1_even_spacing.json')

        cache_key = f"{selected_scenario_file}_{weights['individual']}_{weights['operator']}_{weights['overall']}_{enable_optimizations}_{unlimited_time}"

    

    # Show configuration summary at the top (always display current configuration)

    if scenario and weights:

        with st.expander("Configuration Details", expanded=False):

            # Show scenario name/type

            selected_scenario_file = st.session_state.get('selected_scenario_file', 'N/A')

            if use_dynamic:

                st.markdown(f"**Scenario:** {scenario.name} (Base: {selected_scenario_file})")

            else:

                st.markdown(f"**Scenario:** {scenario.name} ({selected_scenario_file})")

            

            col1, col2, col3 = st.columns(3)

            # Show bus breakdown for all scenarios

            if use_dynamic:

                # Read from widget keys for dynamic scenarios

                num_forward = st.session_state.get('num_forward_input', 10)

                num_reverse = st.session_state.get('num_reverse_input', 10)

                col1.metric("Buses", f"{num_forward}F + {num_reverse}R = {num_forward + num_reverse}")

            else:

                # Count forward and reverse buses for static scenarios

                num_forward = sum(1 for bus in scenario.buses if bus.direction == 'BK')

                num_reverse = sum(1 for bus in scenario.buses if bus.direction == 'KB')

                col1.metric("Buses", f"{num_forward}F + {num_reverse}R = {len(scenario.buses)}")

            col2.metric("Stations", len(config.STATIONS))

            col3.metric("Optimizations", "Enabled" if enable_optimizations else "Disabled")

            

            st.markdown(f"""

            **Weights:**

            - Individual: {weights['individual']}

            - Operator: {weights['operator']}

            - Overall: {weights['overall']}

            

            **Time Limit:** {config.SOLVER_TIME_LIMIT_SECONDS}s

            

            **Cache Key:** `{cache_key[:80]}{'...' if len(cache_key) > 80 else ''}`

            

            *Note: Different scenarios or configurations create unique cache entries*

            """)

    

    # Show carousel after configuration details

    from ui.carousels import show_fact_carousel

    show_fact_carousel()

    

    # Check if configuration has changed since last solve

    # If so, clear previous results and wait for user to click run

    if 'last_cache_key' in st.session_state and st.session_state['last_cache_key'] != cache_key:

        # Configuration changed, clear results

        if 'solver_result' in st.session_state:

            del st.session_state['solver_result']

        if 'solver_scenario' in st.session_state:

            del st.session_state['solver_scenario']

        if 'solver_weights' in st.session_state:

            del st.session_state['solver_weights']

    

    # Display estimated solve time

    if unlimited_time:

        st.info("Running with unlimited time - may take significantly longer for optimal solution")

    else:

        st.info("Guaranteed feasible solution within time limit. Enable unlimited time for optimal solution on larger datasets.")

    

    # Display optimization status (shown before solver runs)

    if enable_optimizations:

        st.info("Optimizations enabled")

    

    # Only run solver when Run button is clicked

    if not run_clicked and 'solver_result' not in st.session_state:

        st.info("Click the 'Run solver' button in the sidebar to start the solver")

        st.stop()

    

    # Run scheduler with progress indicators (only when button clicked)

    if run_clicked:

        try:

            # Set solver running state

            st.session_state['solver_running'] = True

            

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

            

            # Run solver with spinner (caching handled inside run_scheduler)

            with st.spinner("Solving scheduling problem using CP-SAT solver..."):

                if use_dynamic:

                    # Use run_scheduler with caching for dynamic mode too
                    result, scenario = run_scheduler(scenario, weights, enable_optimizations, unlimited_time, cache_key=cache_key)

                else:

                    # Get the actual selected scenario file from session state (set by sidebar)

                    selected_scenario_file = st.session_state.get('selected_scenario_file', 'scenario_1_even_spacing.json')

                    result, scenario = run_scheduler(selected_scenario_file, weights, enable_optimizations, unlimited_time, cache_key=cache_key)

            

            progress_bar.progress(100)

            status_text.text("Solution found!")

            

            # Clear progress indicators

            progress_bar.empty()

            status_text.empty()

            

            # Store result in session state for persistence

            st.session_state['solver_result'] = result

            st.session_state['solver_scenario'] = scenario

            st.session_state['solver_weights'] = weights

            # Store cache key to detect configuration changes

            st.session_state['last_cache_key'] = cache_key

            

            # Set solver running state to False

            st.session_state['solver_running'] = False

            

            # Display solve status

            if result.solver_status == "OPTIMAL":

                st.success(f"Solver found OPTIMAL solution in {result.solve_time_seconds:.2f} seconds")

            elif result.solver_status == "FEASIBLE":

                st.warning(f"Solver found FEASIBLE solution in {result.solve_time_seconds:.2f} seconds (time limit reached)")

            else:

                st.error(f"Solver status: {result.solver_status}")

        

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

