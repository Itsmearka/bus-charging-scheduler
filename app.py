"""
Bus Charging Scheduler - Streamlit UI
Interactive web application for visualizing and tuning charging schedules.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import random
import time
from src.loader import load_scenario, list_available_scenarios, get_scenario_config
from src.scheduler import BusChargingScheduler
from src.utils import minutes_to_time, generate_dynamic_buses


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


@st.cache_data
def get_scenarios():
    """Get list of available scenarios with caching."""
    return list_available_scenarios()


@st.cache_data
def load_scenario_cached(scenario_path):
    """Load scenario with caching."""
    return load_scenario(scenario_path)


@st.cache_data
def run_scheduler(_scenario_input, weights, enable_optimizations, unlimited_time=False, _cache_key=None):
    """Run scheduler with caching based on scenario, weights, and optimization flag."""
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
    """Run scheduler without caching (for dynamic scenarios)."""
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


def get_interesting_fact():
    """Return a random interesting fact about electric buses or CP-SAT."""
    facts = [
        "CP-SAT can handle millions of variables and constraints efficiently",
        "Electric buses can save up to 70% on fuel costs compared to diesel",
        "Fast charging takes 25 minutes for full charge in this system",
        "This scheduler uses Google's OR-Tools CP-SAT library",
        "Electric buses have zero tailpipe emissions",
        "CP-SAT is used by major companies for logistics optimization",
        "Battery range is 240km for buses in this system",
        "The solver uses constraint programming to find optimal schedules",
        "Electric buses are quieter than traditional diesel buses"
    ]
    return random.choice(facts)


def show_fact_carousel():
    """Display a carousel of interesting facts using HTML/JavaScript to avoid Streamlit reruns."""
    facts = [
        "CP-SAT can handle millions of variables and constraints efficiently",
        "Electric buses can save up to 70% on fuel costs compared to diesel",
        "Fast charging takes 25 minutes for full charge in this system",
        "This scheduler uses Google's OR-Tools CP-SAT library",
        "Electric buses have zero tailpipe emissions",
        "CP-SAT is used by major companies for logistics optimization",
        "Battery range is 240km for buses in this system",
        "The solver uses constraint programming to find optimal schedules",
        "Electric buses are quieter than traditional diesel buses"
    ]
    
    # Create HTML/JavaScript carousel with beautiful styling
    html_code = f"""
    <div style="padding: 0.25rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 0.75rem; margin: 0; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2); height: 100%; box-sizing: border-box; padding-inline: 1rem;">
        <div style="display: flex; align-items: center; justify-content: center; gap: 15px; height: 100%;">
            <button onclick="prevFact()" style="padding: 10px 18px; cursor: pointer; background: rgba(255, 255, 255, 0.2); color: white; border: 2px solid rgba(255, 255, 255, 0.3); border-radius: 8px; font-size: 16px; transition: all 0.3s ease; backdrop-filter: blur(10px);">←</button>
            <div style="flex: 1; text-align: center;">
                <div style="color: white; font-weight: 600; margin-bottom: 6px; font-size: 14px; text-transform: uppercase; letter-spacing: 1px;">Did you know?</div>
                <div id="fact-display" style="color: rgba(255, 255, 255, 0.95); font-size: 14px; line-height: 1.5; min-height: 35px; display: flex; align-items: center; justify-content: center;">{facts[0]}</div>
                <div id="fact-counter" style="color: rgba(255, 255, 255, 0.7); font-size: 12px; margin-top: 8px; font-weight: 500;">Fact 1 of {len(facts)}</div>
            </div>
            <button onclick="nextFact()" style="padding: 10px 18px; cursor: pointer; background: rgba(255, 255, 255, 0.2); color: white; border: 2px solid rgba(255, 255, 255, 0.3); border-radius: 8px; font-size: 16px; transition: all 0.3s ease; backdrop-filter: blur(10px);">→</button>
        </div>
    </div>
    <style>
        html {{
            background-color: #0e1117;
        }}
        * {{
            box-sizing: border-box;
        }}
        button:hover {{
            background: rgba(255, 255, 255, 0.3) !important;
            transform: scale(1.05);
        }}
        #fact-display {{
            transition: opacity 0.3s ease;
        }}
    </style>
    <script>
        var facts = {facts};
        var currentIndex = 0;
        var autoRotateInterval = null;
        
        function updateDisplay() {{
            var factDisplay = document.getElementById('fact-display');
            factDisplay.style.opacity = '0';
            setTimeout(function() {{
                factDisplay.textContent = facts[currentIndex];
                factDisplay.style.opacity = '1';
            }}, 150);
            
            document.getElementById('fact-counter').textContent = 'Fact ' + (currentIndex + 1) + ' of ' + facts.length;
        }}
        
        function nextFact() {{
            currentIndex = (currentIndex + 1) % facts.length;
            updateDisplay();
        }}
        
        function prevFact() {{
            currentIndex = (currentIndex - 1 + facts.length) % facts.length;
            updateDisplay();
        }}
        
        // Start automatic rotation every 5 seconds
        function startAutoRotate() {{
            if (autoRotateInterval) {{
                clearInterval(autoRotateInterval);
            }}
            autoRotateInterval = setInterval(nextFact, 5000);
        }}
        
        // Start auto-rotation on load
        startAutoRotate();
    </script>
    """
    
    st.components.v1.html(html_code, height=100)


def main():
    """Main application function."""
    st.title("Bus Charging Scheduler")
    st.markdown("Electric bus charging optimization using CP-SAT constraint programming")
    
    # Sidebar: Scenario selector
    st.sidebar.header("Configuration")
    
    # Show interesting fact carousel in sidebar
    show_fact_carousel()
    
    # Get available scenarios
    scenario_files = get_scenarios()
    
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
    
    # Optimizations toggle
    enable_optimizations = st.sidebar.checkbox(
        "Enable Optimizations",
        value=False,
        help="Enable time-window decomposition and station filtering for larger scenarios"
    )
    
    # Dynamic Bus Configuration Section
    st.sidebar.markdown("---")
    st.sidebar.subheader("Dynamic Bus Configuration")
    
    use_dynamic = st.sidebar.checkbox("Use Dynamic Bus Generation", value=False)
    
    if use_dynamic:
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
        
        # Generate dynamic scenario
        dynamic_buses = generate_dynamic_buses(
            num_forward=num_forward,
            num_reverse=num_reverse,
            start_time_forward=start_time_forward.strftime("%H:%M"),
            start_time_reverse=start_time_reverse.strftime("%H:%M"),
            interval_minutes=interval_minutes
        )
        
        # Create in-memory scenario
        from src.models import Scenario
        scenario = Scenario(
            name=f"Dynamic - {num_forward}F/{num_reverse}R",
            description=f"Dynamically generated: {num_forward} forward, {num_reverse} reverse buses",
            weights={'individual': 1.0, 'operator': 1.0, 'overall': 1.0},
            buses=dynamic_buses
        )
        individual_weight = 1.0
        operator_weight = 1.0
        overall_weight = 1.0
        enable_optimizations = False
    else:
        # Load selected scenario
        scenario = load_scenario_cached(selected_scenario_file)
    
    # Display scenario metadata (only if not dynamic)
    if not use_dynamic:
        st.sidebar.subheader("Scenario Details")
        st.sidebar.write(f"**Name:** {scenario.name}")
        st.sidebar.write(f"**Buses:** {len(scenario.buses)}")
        st.sidebar.write(f"**Description:** {scenario.description}")
    
    # Weight tuning
    st.sidebar.subheader("Optimization Weights")
    
    # Get current weights
    if use_dynamic:
        individual_weight = 1.0
        operator_weight = 1.0
        overall_weight = 1.0
    else:
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
    
    # Remove time limit toggle
    unlimited_time = st.sidebar.checkbox(
        "Remove Time Limit (Run Until Optimal)",
        value=False,
        help="Disable solver time limit to find guaranteed optimal solution (may take very long)"
    )
    
    # Combine weights into dictionary for scheduler
    weights = {
        'individual': individual_weight,
        'operator': operator_weight,
        'overall': overall_weight
    }
    
    # Create cache key for current configuration
    cache_key = f"{selected_scenario_file}_{weights['individual']}_{weights['operator']}_{weights['overall']}_{enable_optimizations}_{unlimited_time}"
    
    # Display estimated solve time
    import config
    if unlimited_time:
        st.info("Running with unlimited time - may take significantly longer for optimal solution")
    else:
        st.info("Guaranteed feasible solution within time limit. Enable unlimited time for optimal solution on larger datasets.")
    
    # Run scheduler with progress indicators
    try:
        # Check if we have cached results for this configuration
        if 'solver_cache' in st.session_state and cache_key in st.session_state['solver_cache']:
            result = st.session_state['solver_cache'][cache_key]['result']
            scenario = st.session_state['solver_cache'][cache_key]['scenario']
            st.success("Using cached solution from previous run")
        else:
            # Show configuration summary at the top
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
        
        # Display solve status
        if result.solver_status == "OPTIMAL":
            st.success(f"Solver found OPTIMAL solution in {result.solve_time_seconds:.2f} seconds")
        elif result.solver_status == "FEASIBLE":
            st.warning(f"Solver found FEASIBLE solution in {result.solve_time_seconds:.2f} seconds (time limit reached)")
        else:
            st.error(f"Solver status: {result.solver_status}")
        
        # Display optimization status
        if enable_optimizations:
            st.info("Phase 2 optimizations enabled")
    
    except Exception as e:
        st.error(f"Error running scheduler: {e}")
        st.stop()
    
    # Create tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["Scenario Input", "Bus Timetables", "Station Queues", "Metrics"])
    
    # Tab 1: Scenario Input
    with tab1:
        st.header("Scenario Input Data")
        
        # Display weights
        st.subheader("Optimization Weights")
        col1, col2, col3 = st.columns(3)
        col1.metric("Individual", individual_weight)
        col2.metric("Operator", operator_weight)
        col3.metric("Overall", overall_weight)
        
        # Display bus schedule
        st.subheader("Bus Schedule")
        buses_data = []
        for bus in scenario.buses:
            buses_data.append({
                "Bus ID": bus.id,
                "Operator": bus.operator,
                "Direction": "BK" if bus.direction == "BK" else "KB",
                "Departure Time": minutes_to_time(bus.departure_time_minutes)
            })
        
        df_buses = pd.DataFrame(buses_data)
        st.dataframe(df_buses, use_container_width=True)
        
        # Display route information
        st.subheader("Route Information")
        config = get_scenario_config(scenario)
        
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Route:** Bengaluru → A → B → C → D → Kochi")
            st.write(f"**Total Distance:** {config['total_route_distance_km']} km")
            st.write(f"**Battery Range:** {config['battery_range_km']} km")
            st.write(f"**Charging Time:** {config['charging_time_minutes']} minutes")
        
        with col2:
            st.write("**Stations:**")
            for station in config['stations']:
                location = config['station_locations_km'][station]
                chargers = config['chargers_per_station'][station]
                st.write(f"  - {station}: {location} km from Bengaluru ({chargers} charger)")
        
        # Display route segments with distances
        st.subheader("Route Segments")
        segments = [
            ("Bengaluru", "A", 100),
            ("A", "B", 120),
            ("B", "C", 100),
            ("C", "D", 120),
            ("D", "Kochi", 100)
        ]
        
        for from_loc, to_loc, distance in segments:
            st.write(f"  - {from_loc} → {to_loc}: {distance} km")
    
    # Tab 2: Bus Timetables
    with tab2:
        st.header("Bus Timetables")
        st.write("Charging plans for each bus")
        
        # Create data for all buses
        timetable_data = []
        for plan in result.plans:
            for event in plan.events:
                timetable_data.append({
                    "Bus ID": plan.bus_id,
                    "Station": event.station_id,
                    "Arrival": minutes_to_time(event.arrival_time_minutes),
                    "Start": minutes_to_time(event.start_time_minutes),
                    "End": minutes_to_time(event.end_time_minutes),
                    "Wait (min)": event.wait_time_minutes
                })
        
        if timetable_data:
            df_timetable = pd.DataFrame(timetable_data)
            st.dataframe(df_timetable, use_container_width=True)
        else:
            st.info("No charging events in this scenario")
        
        # Display summary by bus
        st.subheader("Summary by Bus")
        summary_data = []
        for plan in result.plans:
            summary_data.append({
                "Bus ID": plan.bus_id,
                "Departure": minutes_to_time(plan.departure_time_minutes),
                "Arrival": minutes_to_time(plan.arrival_time_minutes),
                "Total Wait (min)": plan.total_wait_time_minutes,
                "Trip Time (min)": plan.arrival_time_minutes - plan.departure_time_minutes,
                "Charging Stops": len(plan.events)
            })
        
        df_summary = pd.DataFrame(summary_data)
        st.dataframe(df_summary, use_container_width=True)
    
    # Tab 3: Station Queues
    with tab3:
        st.header("Station Queues")
        st.write("Charging order at each station")
        
        stations = ['A', 'B', 'C', 'D']
        
        for station in stations:
            st.subheader(f"Station {station}")
            
            # Collect all charging events at this station
            events_at_station = []
            for plan in result.plans:
                for event in plan.events:
                    if event.station_id == station:
                        events_at_station.append({
                            "Bus ID": event.bus_id,
                            "Arrival": minutes_to_time(event.arrival_time_minutes),
                            "Start": minutes_to_time(event.start_time_minutes),
                            "End": minutes_to_time(event.end_time_minutes),
                            "Wait (min)": event.wait_time_minutes
                        })
            
            # Sort by start time
            events_at_station.sort(key=lambda x: x['Start'])
            
            if events_at_station:
                df_station = pd.DataFrame(events_at_station)
                st.dataframe(df_station, use_container_width=True)
            else:
                st.info(f"No charging events at Station {station}")
    
    # Tab 4: Metrics
    with tab4:
        st.header("Metrics Summary")
        
        # Overall metrics
        st.subheader("Overall System Metrics")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Wait Time", f"{result.total_wait_time_minutes} min")
        col2.metric("Average Wait", f"{result.average_wait_time_minutes:.2f} min")
        col3.metric("Max Wait", f"{result.max_wait_time_minutes} min")
        col4.metric("Solve Time", f"{result.solve_time_seconds:.2f} s")
        
        # Operator-level metrics
        st.subheader("Operator Metrics")
        operators = {}
        for plan in result.plans:
            bus = next(b for b in scenario.buses if b.id == plan.bus_id)
            operator = bus.operator
            
            if operator not in operators:
                operators[operator] = []
            operators[operator].append(plan)
        
        operator_data = []
        for operator, plans in operators.items():
            total_wait = sum(p.total_wait_time_minutes for p in plans)
            avg_wait = total_wait / len(plans)
            max_wait = max(p.total_wait_time_minutes for p in plans)
            
            operator_data.append({
                "Operator": operator,
                "Buses": len(plans),
                "Total Wait (min)": total_wait,
                "Average Wait (min)": f"{avg_wait:.2f}",
                "Max Wait (min)": max_wait
            })
        
        df_operators = pd.DataFrame(operator_data)
        st.dataframe(df_operators, use_container_width=True)
        
        # Station utilization
        st.subheader("Station Utilization")
        config = get_scenario_config(scenario)
        
        utilization_data = []
        for station in stations:
            # Count charging events at this station
            event_count = 0
            total_charging_time = 0
            
            for plan in result.plans:
                for event in plan.events:
                    if event.station_id == station:
                        event_count += 1
                        total_charging_time += (event.end_time_minutes - event.start_time_minutes)
            
            chargers = config['chargers_per_station'][station]
            utilization_data.append({
                "Station": station,
                "Chargers": chargers,
                "Charging Events": event_count,
                "Total Charging Time (min)": total_charging_time
            })
        
        df_utilization = pd.DataFrame(utilization_data)
        st.dataframe(df_utilization, use_container_width=True)


if __name__ == "__main__":
    main()
