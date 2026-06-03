"""
Bus generation utility functions for Bus Charging Scheduler.
Provides dynamic bus generation based on configuration.
"""

from typing import List
import config
from src.models import Bus
from src.utils.time import time_to_minutes


def generate_dynamic_buses(
    num_forward: int,
    num_reverse: int,
    start_time_forward: str,
    start_time_reverse: str,
    interval_minutes: int
) -> List[Bus]:
    """
    Generate buses dynamically based on configuration.
    
    Args:
        num_forward: Number of forward (BK) buses
        num_reverse: Number of reverse (KB) buses
        start_time_forward: Start time for forward buses (HH:MM)
        start_time_reverse: Start time for reverse buses (HH:MM)
        interval_minutes: Departure interval in minutes
    
    Returns:
        List of Bus objects
    """
    buses = []
    operators = config.OPERATORS
    
    # Convert start times to minutes
    start_forward_min = time_to_minutes(start_time_forward)
    start_reverse_min = time_to_minutes(start_time_reverse)
    
    # Generate forward buses
    for i in range(1, num_forward + 1):
        operator = operators[(i - 1) % len(operators)]
        departure_min = start_forward_min + (i - 1) * interval_minutes
        buses.append(Bus(
            id=f"bus_forward_{i}",
            operator=operator,
            direction="BK",
            departure_time_minutes=departure_min
        ))
    
    # Generate reverse buses
    for i in range(1, num_reverse + 1):
        operator = operators[(i - 1) % len(operators)]
        departure_min = start_reverse_min + (i - 1) * interval_minutes
        buses.append(Bus(
            id=f"bus_reverse_{i}",
            operator=operator,
            direction="KB",
            departure_time_minutes=departure_min
        ))
    
    return buses
