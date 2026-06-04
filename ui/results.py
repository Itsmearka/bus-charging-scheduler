"""
UI Results Module
Results display components for timetables, station queues, and metrics.
"""

import pandas as pd
import streamlit as st
from src.utils.time import minutes_to_time
from src.loader import get_scenario_config


def render_results(result, scenario, weights):
    """
    Render all results tabs.
    
    Args:
        result: Scheduler result object
        scenario: Scenario object
        weights: Weights dictionary
    """
    # Create tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["Scenario Input", "Bus Timetables", "Station Queues", "Metrics"])
    
    # Tab 1: Scenario Input
    with tab1:
        render_scenario_input_tab(scenario, weights)
    
    # Tab 2: Bus Timetables
    with tab2:
        render_bus_timetables_tab(result)
    
    # Tab 3: Station Queues
    with tab3:
        render_station_queues_tab(result)
    
    # Tab 4: Metrics
    with tab4:
        render_metrics_tab(result, scenario)


def render_scenario_input_tab(scenario, weights):
    """
    Render scenario input data tab.
    
    Args:
        scenario: Scenario object
        weights: Weights dictionary
    """
    st.header("Scenario Input Data")
    
    # Display weights
    st.subheader("Optimization Weights")
    col1, col2, col3 = st.columns(3)
    col1.metric("Individual", weights['individual'])
    col2.metric("Operator", weights['operator'])
    col3.metric("Overall", weights['overall'])
    
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
        st.write("**Route:** Bengaluru -> A -> B -> C -> D -> Kochi")
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
        st.write(f"  - {from_loc} -> {to_loc}: {distance} km")


def render_bus_timetables_tab(result):
    """
    Render bus timetables tab.
    
    Args:
        result: Scheduler result object
    """
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


def render_station_queues_tab(result):
    """
    Render station queues tab.
    
    Args:
        result: Scheduler result object
    """
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


def render_metrics_tab(result, scenario):
    """
    Render metrics summary tab.
    
    Args:
        result: Scheduler result object
        scenario: Scenario object
    """
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
    for station in ['A', 'B', 'C', 'D']:
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
