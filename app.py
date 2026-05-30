"""
Bus Charging Scheduler - Streamlit UI

This is the main application interface for the bus charging scheduler.
It allows users to select scenarios, view input data, and see scheduling results.
"""

import streamlit as st
import pandas as pd
import json
from datetime import datetime
from typing import List, Dict

from src.scenario_loader import ScenarioLoader
from src.scheduler import Scheduler
from src.utils import minutes_to_time, format_duration
from src.models import WorldConfig, Segment, Route, Station, Bus, Scenario, Direction


def load_config():
    """
    Load configuration from config.json file.
    
    Returns:
        dict: Configuration dictionary
    """
    try:
        with open('config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Return default config if file doesn't exist
        return {
            "world_config": {
                "battery_range_km": 240.0,
                "charging_time_min": 25.0,
                "travel_speed_kmh": 60.0
            },
            "station_config": {
                "default_chargers_per_station": 1
            },
            "bus_config": {
                "default_passengers_per_bus": 40,
                "default_battery_capacity_km": 240.0
            },
            "fleet_config": {
                "default_num_buses_per_direction": 10,
                "default_departure_interval_min": 15
            },
            "optimization_weights": {
                "individual": 1.0,
                "operator": 1.0,
                "overall": 1.0
            }
        }


def create_custom_scenario(
    station_names: List[str],
    distances: List[float],
    battery_range_km: float,
    charging_time_min: float,
    travel_speed_kmh: float,
    chargers_per_station: int,
    num_buses_per_direction: int,
    departure_interval_min: int,
    weights: Dict[str, float]
) -> Scenario:
    """
    Create a custom scenario from UI inputs.
    
    Args:
        station_names: List of station names in order
        distances: List of distances between consecutive stations
        battery_range_km: Maximum battery range
        charging_time_min: Charging time in minutes
        travel_speed_kmh: Travel speed in km/h
        chargers_per_station: Number of chargers per station
        num_buses_per_direction: Number of buses in each direction
        departure_interval_min: Departure interval in minutes
        weights: Optimization weights
        
    Returns:
        Custom Scenario object
    """
    # Create world config
    world_config = WorldConfig(
        battery_range_km=battery_range_km,
        charging_time_min=charging_time_min,
        travel_speed_kmh=travel_speed_kmh,
        default_weights=weights
    )
    
    # Create segments
    segments = []
    for i in range(len(station_names) - 1):
        segment = Segment(
            from_station=station_names[i],
            to_station=station_names[i + 1],
            distance_km=distances[i]
        )
        segments.append(segment)
    
    # Calculate total distance
    total_distance = sum(distances)
    
    # Create route
    route = Route(
        route_id="custom_route",
        name="Custom Route",
        segments=segments,
        total_distance=total_distance
    )
    
    # Create stations (exclude first and last as they are start/end cities, not charging stations)
    stations = {}
    for i, station_name in enumerate(station_names):
        # Skip first and last stations - they are start/end cities, not charging stations
        if i == 0 or i == len(station_names) - 1:
            continue
        station = Station(
            station_id=station_name,
            name=station_name,
            num_chargers=chargers_per_station
        )
        stations[station_name] = station
    
    # Create buses
    buses = []
    operators = ["kpn", "freshbus", "flixbus"]
    
    # Forward direction buses
    for i in range(num_buses_per_direction):
        departure_time = i * departure_interval_min
        departure_time_str = minutes_to_time(departure_time)
        bus = Bus(
            bus_id=f"bus-F-{i+1:02d}",
            operator=operators[i % len(operators)],
            route_id="custom_route",
            direction=Direction.FORWARD,
            departure_time=departure_time_str
        )
        buses.append(bus)
    
    # Reverse direction buses
    for i in range(num_buses_per_direction):
        departure_time = i * departure_interval_min
        departure_time_str = minutes_to_time(departure_time)
        bus = Bus(
            bus_id=f"bus-R-{i+1:02d}",
            operator=operators[i % len(operators)],
            route_id="custom_route",
            direction=Direction.REVERSE,
            departure_time=departure_time_str
        )
        buses.append(bus)
    
    # Create scenario
    scenario = Scenario(
        metadata={
            "name": "Custom Route",
            "description": f"Custom route with {len(station_names)} stations",
            "version": "1.0"
        },
        world_config=world_config,
        routes={"custom_route": route},
        stations=stations,
        buses=buses,
        weights=weights
    )
    
    return scenario


def main():
    """
    Main Streamlit application.
    """
    st.set_page_config(
        page_title="Bus Charging Scheduler",
        page_icon="🚌",
        layout="wide"
    )
    
    st.title("Bus Charging Scheduler")
    st.markdown("---")
    
    # Initialize session state
    if 'scenario' not in st.session_state:
        st.session_state.scenario = None
    if 'result' not in st.session_state:
        st.session_state.result = None
    if 'custom_stations' not in st.session_state:
        st.session_state.custom_stations = ["Bengaluru", "A", "B", "C", "D", "Kochi"]
    if 'custom_distances' not in st.session_state:
        st.session_state.custom_distances = [100.0, 120.0, 100.0, 120.0, 100.0]
    
    # Load configuration
    config = load_config()
    
    # Sidebar - Configuration
    st.sidebar.header("Configuration")
    
    # World Configuration
    st.sidebar.subheader("World Settings")
    battery_range = st.sidebar.slider(
        "Battery Range (km)",
        min_value=100.0,
        max_value=500.0,
        value=config.get("world_config", {}).get("battery_range_km", 240.0),
        step=10.0,
        help="Maximum distance a bus can travel on full charge"
    )
    
    charging_time = st.sidebar.slider(
        "Charging Time (min)",
        min_value=10.0,
        max_value=60.0,
        value=config.get("world_config", {}).get("charging_time_min", 25.0),
        step=5.0,
        help="Time required to fully charge a bus"
    )
    
    travel_speed = st.sidebar.slider(
        "Travel Speed (km/h)",
        min_value=30.0,
        max_value=120.0,
        value=config.get("world_config", {}).get("travel_speed_kmh", 60.0),
        step=5.0,
        help="Average speed of buses"
    )
    
    # Fleet Configuration
    st.sidebar.subheader("Fleet Settings")
    num_buses_per_direction = st.sidebar.slider(
        "Buses per Direction",
        min_value=1,
        max_value=50,
        value=config.get("fleet_config", {}).get("default_num_buses_per_direction", 10),
        step=1,
        help="Number of buses in each direction"
    )
    
    departure_interval = st.sidebar.slider(
        "Departure Interval (min)",
        min_value=5,
        max_value=60,
        value=config.get("fleet_config", {}).get("default_departure_interval_min", 15),
        step=5,
        help="Time between bus departures"
    )
    
    passengers_per_bus = st.sidebar.slider(
        "Passengers per Bus",
        min_value=10,
        max_value=80,
        value=config.get("bus_config", {}).get("default_passengers_per_bus", 40),
        step=5,
        help="Number of passengers each bus can carry"
    )
    
    # Station Configuration
    st.sidebar.subheader("Station Settings")
    chargers_per_station = st.sidebar.slider(
        "Chargers per Station",
        min_value=1,
        max_value=10,
        value=config.get("station_config", {}).get("default_chargers_per_station", 1),
        step=1,
        help="Number of charging ports at each station"
    )
    
    # Optimization Weights
    st.sidebar.markdown("---")
    st.sidebar.subheader("Optimization Weights")
    individual_weight = st.sidebar.slider(
        "Individual Weight",
        min_value=0.0,
        max_value=5.0,
        value=config.get("optimization_weights", {}).get("individual", 1.0),
        step=0.1,
        help="Weight for minimizing wait time per bus"
    )
    operator_weight = st.sidebar.slider(
        "Operator Weight",
        min_value=0.0,
        max_value=5.0,
        value=config.get("optimization_weights", {}).get("operator", 1.0),
        step=0.1,
        help="Weight for balancing charging across operator fleets"
    )
    overall_weight = st.sidebar.slider(
        "Overall Weight",
        min_value=0.0,
        max_value=5.0,
        value=config.get("optimization_weights", {}).get("overall", 1.0),
        step=0.1,
        help="Weight for minimizing total network time"
    )
    
    st.sidebar.info(
        "**Individual**: Minimize wait time per bus\n"
        "**Operator**: Balance charging across operator fleets\n"
        "**Overall**: Minimize total network time"
    )
    
    st.sidebar.markdown("---")
    
    # Scenario Selection
    st.sidebar.subheader("Scenario Selection")
    scenario_mode = st.sidebar.radio(
        "Scenario Mode",
        ["Pre-built Scenarios", "Custom Route"]
    )
    
    if scenario_mode == "Pre-built Scenarios":
        loader = ScenarioLoader("data/scenarios")
        scenarios = loader.list_scenarios()
        
        # Make scenario names more descriptive
        scenario_names = {
            "scenario_1_even_spacing": "Scenario 1: Even Spacing (15 min interval)",
            "scenario_2_bunched_start": "Scenario 2: Bunched Start (8 min interval)",
            "scenario_3_asymmetric_load": "Scenario 3: Asymmetric Load (10 vs 4 buses)",
            "scenario_4_operator_heavy": "Scenario 4: Operator Heavy (KPN dominant)",
            "scenario_5_worst_case": "Scenario 5: Worst Case (72 min window)",
            "scenario_6_scalability_test": "Scenario 6: Multi-Charger (2 ports/station)",
            "scenario_7_many_buses": "Scenario 7: Many Buses (40 buses total)"
        }
        
        display_scenarios = [scenario_names.get(s, s) for s in scenarios]
        
        selected_display = st.sidebar.selectbox(
            "Select Scenario",
            display_scenarios,
            index=0 if display_scenarios else None
        )
        
        # Map back to original scenario name
        selected_scenario = None
        for orig, disp in scenario_names.items():
            if disp == selected_display:
                selected_scenario = orig
                break
        if selected_scenario is None:
            selected_scenario = selected_display
    else:
        # Custom Route Configuration
        st.sidebar.subheader("Custom Route Configuration")
        
        # Display current stations
        st.sidebar.write("Current Stations:")
        for i, station in enumerate(st.session_state.custom_stations):
            st.sidebar.write(f"{i+1}. {station}")
        
        # Station insertion mode
        st.sidebar.subheader("Add Station")
        insert_mode = st.sidebar.radio(
            "Insert Mode",
            ["Add at End", "Insert Between"]
        )
        
        if insert_mode == "Add at End":
            new_station = st.sidebar.text_input("Add new station:")
            add_station_button = st.sidebar.button("Add Station")
            
            if add_station_button and new_station:
                st.session_state.custom_stations.append(new_station)
                st.session_state.custom_distances.append(100.0)  # Default distance
                st.rerun()
        else:
            # Insert between stations
            new_station = st.sidebar.text_input("New station name:")
            
            # Select position to insert
            insert_positions = [f"After {st.session_state.custom_stations[i]}" for i in range(len(st.session_state.custom_stations) - 1)]
            insert_positions.append("At End")
            selected_position = st.sidebar.selectbox(
                "Insert position:",
                insert_positions
            )
            
            # Distance split configuration
            st.sidebar.write("Distance Configuration:")
            if selected_position != "At End":
                insert_index = insert_positions.index(selected_position)
                original_distance = st.session_state.custom_distances[insert_index]
                st.sidebar.write(f"Original distance: {original_distance} km")
                
                split_ratio = st.sidebar.slider(
                    "Split ratio (first segment : second segment)",
                    min_value=0.1,
                    max_value=0.9,
                    value=0.5,
                    step=0.1,
                    help="Ratio of distance for the first segment"
                )
                
                first_distance = original_distance * split_ratio
                second_distance = original_distance * (1 - split_ratio)
                
                st.sidebar.write(f"First segment: {first_distance:.1f} km")
                st.sidebar.write(f"Second segment: {second_distance:.1f} km")
            else:
                first_distance = 100.0
                second_distance = 100.0
            
            insert_button = st.sidebar.button("Insert Station")
            
            if insert_button and new_station:
                if selected_position == "At End":
                    st.session_state.custom_stations.append(new_station)
                    st.session_state.custom_distances.append(100.0)
                else:
                    insert_index = insert_positions.index(selected_position)
                    # Insert station
                    st.session_state.custom_stations.insert(insert_index + 1, new_station)
                    # Split distance
                    st.session_state.custom_distances.pop(insert_index)
                    st.session_state.custom_distances.insert(insert_index, first_distance)
                    st.session_state.custom_distances.insert(insert_index + 1, second_distance)
                st.rerun()
        
        # Remove last station
        if len(st.session_state.custom_stations) > 2:
            remove_station_button = st.sidebar.button("Remove Last Station")
            if remove_station_button:
                st.session_state.custom_stations.pop()
                st.session_state.custom_distances.pop()
                st.rerun()
        
        # Configure distances
        st.sidebar.subheader("Distance Configuration")
        for i in range(len(st.session_state.custom_distances)):
            distance = st.sidebar.number_input(
                f"Distance {st.session_state.custom_stations[i]} -> {st.session_state.custom_stations[i+1]} (km)",
                min_value=10.0,
                max_value=500.0,
                value=st.session_state.custom_distances[i],
                step=10.0,
                key=f"distance_{i}"
            )
            st.session_state.custom_distances[i] = distance
        
        selected_scenario = "custom"
    
    # Run scheduler button
    run_button = st.sidebar.button("Run Scheduler", type="primary")
    
    # Load and run scenario
    if run_button or (selected_scenario and (st.session_state.get('last_run_scenario') != selected_scenario or st.session_state.get('result') is None)):
        try:
            # Show loading indicator
            scenario_name = selected_scenario if selected_scenario != "custom" else "Custom Route"
            with st.spinner(f"Updating results for {scenario_name}..."):
                import time
                time.sleep(1)  # Show loading for at least 1 second
                
                if selected_scenario == "custom":
                    # Create custom scenario
                    scenario = create_custom_scenario(
                        station_names=st.session_state.custom_stations,
                        distances=st.session_state.custom_distances,
                        battery_range_km=battery_range,
                        charging_time_min=charging_time,
                        travel_speed_kmh=travel_speed,
                        chargers_per_station=chargers_per_station,
                        num_buses_per_direction=num_buses_per_direction,
                        departure_interval_min=departure_interval,
                        weights={
                            "individual": individual_weight,
                            "operator": operator_weight,
                            "overall": overall_weight
                        }
                    )
                else:
                    # Load pre-built scenario
                    scenario = loader.load_scenario(selected_scenario)
                    
                    # Update world config based on sliders
                    scenario.world_config.battery_range_km = battery_range
                    scenario.world_config.charging_time_min = charging_time
                    scenario.world_config.travel_speed_kmh = travel_speed
                    
                    # Update station config based on chargers slider
                    for station_id, station in scenario.stations.items():
                        station.num_chargers = chargers_per_station
                
                # Run scheduler with single unified approach using scenario weights
                scheduler = Scheduler()
                result = scheduler.schedule(scenario)
                
                # Store configuration values in session state for display
                st.session_state.config_used = {
                    "battery_range_km": battery_range,
                    "charging_time_min": charging_time,
                    "travel_speed_kmh": travel_speed,
                    "num_buses_per_direction": num_buses_per_direction,
                    "departure_interval_min": departure_interval,
                    "passengers_per_bus": passengers_per_bus,
                    "chargers_per_station": chargers_per_station
                }
                
                # Store in session state
                st.session_state.scenario = scenario
                st.session_state.result = result
                st.session_state.last_run_scenario = selected_scenario
            
        except Exception as e:
            st.error(f"Error loading or scheduling scenario: {e}")
            return
    
    # Display results if available
    if st.session_state.result is not None:
        display_results(st.session_state.scenario, st.session_state.result)


def display_results(scenario, result):
    """
    Display the scheduling results.
    
    Args:
        scenario: The scenario that was scheduled
        result: The scheduling result
    """
    # Scenario information
    st.header(f"Scenario: {scenario.metadata['name']}")
    st.subheader(scenario.metadata.get('description', ''))
    
    # Display configuration used
    if 'config_used' in st.session_state:
        config = st.session_state.config_used
        st.subheader("Configuration Used")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Battery Range", f"{config['battery_range_km']} km")
            st.metric("Charging Time", f"{config['charging_time_min']} min")
        with col2:
            st.metric("Travel Speed", f"{config['travel_speed_kmh']} km/h")
            st.metric("Chargers per Station", config['chargers_per_station'])
        with col3:
            st.metric("Buses per Direction", config['num_buses_per_direction'])
            st.metric("Departure Interval", f"{config['departure_interval_min']} min")
        with col4:
            st.metric("Passengers per Bus", config['passengers_per_bus'])
    
    st.markdown("---")
    
    # Scenario metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Number of Buses", len(scenario.buses))
    with col2:
        st.metric("Number of Stations", len(scenario.stations))
    with col3:
        st.metric("Total Distance", f"{sum(s.distance_km for s in list(scenario.routes.values())[0].segments):.0f} km")
    
    st.markdown("---")
    
    # Scenario input data
    st.header("Scenario Input Data")
    
    # Display bus data as table
    bus_data = []
    for bus in scenario.buses:
        bus_data.append({
            "Bus ID": bus.bus_id,
            "Operator": bus.operator,
            "Direction": bus.direction,
            "Departure Time": bus.departure_time
        })
    
    bus_df = pd.DataFrame(bus_data)
    st.dataframe(bus_df, use_container_width=True)
    
    st.markdown("---")
    
    # Metrics
    st.header("Schedule Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Network Time", f"{result.metrics.total_network_time:.0f} min")
    with col2:
        st.metric("Avg Wait per Bus", f"{result.metrics.avg_wait_per_bus:.1f} min")
    with col3:
        st.metric("Max Wait Time", f"{result.metrics.max_wait_time:.1f} min")
    with col4:
        st.metric("Weights Used", str(result.weights_used))
    
    # Operator wait times
    st.subheader("Average Wait per Operator")
    operator_wait_df = pd.DataFrame([
        {"Operator": op, "Avg Wait (min)": f"{wait:.1f}"}
        for op, wait in result.metrics.avg_wait_per_operator.items()
    ])
    st.dataframe(operator_wait_df, use_container_width=True)
    
    st.markdown("---")
    
    # Per-bus timetable
    st.header("Per-Bus Timetable")
    
    bus_schedule_data = []
    for bus_schedule in result.bus_schedules:
        for i, event in enumerate(bus_schedule.charging_events):
            bus_schedule_data.append({
                "Bus ID": bus_schedule.bus_id,
                "Station": event.station_id,
                "Arrival Time": minutes_to_time(event.arrival_time),
                "Charge Start": minutes_to_time(event.charge_start_time),
                "Charge End": minutes_to_time(event.charge_end_time),
                "Wait Time": format_duration(event.wait_time)
            })
        
        # Add final arrival
        bus_schedule_data.append({
            "Bus ID": bus_schedule.bus_id,
            "Station": "Destination",
            "Arrival Time": minutes_to_time(bus_schedule.final_arrival_time),
            "Charge Start": "-",
            "Charge End": "-",
            "Wait Time": format_duration(bus_schedule.total_wait_time)
        })
    
    bus_schedule_df = pd.DataFrame(bus_schedule_data)
    st.dataframe(bus_schedule_df, use_container_width=True)
    
    st.markdown("---")
    
    # Per-station view
    st.header("Per-Station Charging Queue")
    
    # Get start and end cities from route
    start_city = None
    end_city = None
    if scenario.routes:
        # routes is a Dict[str, Route], get first route
        first_route = next(iter(scenario.routes.values()), None)
        if first_route and first_route.segments and len(first_route.segments) > 0:
            start_city = first_route.segments[0].from_station
            end_city = first_route.segments[-1].to_station
    
    # Create list of all locations: start city, charging stations, end city
    station_ids = []
    if start_city:
        station_ids.append(start_city)
    station_ids.extend([s.station_id for s in result.station_schedules])
    if end_city:
        station_ids.append(end_city)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_station_ids = []
    for station_id in station_ids:
        if station_id not in seen:
            seen.add(station_id)
            unique_station_ids.append(station_id)
    
    tabs = st.tabs([f"Station {station_id}" for station_id in unique_station_ids])
    
    for tab, station_id in zip(tabs, unique_station_ids):
        with tab:
            # Find matching station schedule
            station_schedule = next((s for s in result.station_schedules if s.station_id == station_id), None)
            
            if station_schedule and station_schedule.charging_queue:
                station_data = []
                for i, event in enumerate(station_schedule.charging_queue):
                    # Get bus information to determine source and destination
                    bus_id = event['bus_id']
                    bus_info = next((b for b in scenario.buses if b.bus_id == bus_id), None)
                    if bus_info:
                        if bus_info.direction == "forward":
                            source = start_city
                            destination = end_city
                        else:
                            source = end_city
                            destination = start_city
                    else:
                        source = "Unknown"
                        destination = "Unknown"
                    
                    station_data.append({
                        "Order": i + 1,
                        "Bus ID": event['bus_id'],
                        "Source": source,
                        "Destination": destination,
                        "Start Time": minutes_to_time(event['start']),
                        "End Time": minutes_to_time(event['end']),
                        "Wait Time": format_duration(event['wait_time'])
                    })
                
                station_df = pd.DataFrame(station_data)
                st.dataframe(station_df, use_container_width=True)
            else:
                st.info("Not a charging station or no buses charged at this station.")
    
    st.markdown("---")
    
    # Weights used
    st.header("Optimization Weights Used")
    weights_df = pd.DataFrame([
        {"Rule": rule, "Weight": weight}
        for rule, weight in result.weights_used.items()
    ])
    st.dataframe(weights_df, use_container_width=True)


if __name__ == "__main__":
    main()
