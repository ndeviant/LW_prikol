# utils/utils.py

import logging
import random
import time
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)

def random_sleep(base_interval, variation=0.5):
    """
    Sleeps for a random amount of time around the base interval.
    """
    sleep_duration = random.uniform(
        max(0, base_interval - variation),
        base_interval + variation
    )
    logger.debug(f"Sleeping for {sleep_duration:.2f} seconds.")
    time.sleep(sleep_duration)

def get_timestamp():
    """
    Returns the current timestamp as a formatted string.
    """
    return datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")

def check_time_passed(last_check, minutes):
    """
    Checks if a specified number of minutes have passed since the last check.
    """
    current_time = datetime.now()
    if last_check is None or current_time - last_check > timedelta(minutes=minutes):
        logger.debug(f"Time check passed. Last check was at {last_check}.")
        return True, current_time
    logger.debug(f"Time check not passed. Last check was at {last_check}.")
    return False, last_check

def convert_percentage_positions(
    positions_dict: Dict[str, List[str]],
    screen_width: int,
    screen_height: int
) -> Dict[str, Tuple[int, int]]:
    """
    Converts positions specified as percentage strings to actual pixel coordinates.

    Args:
        positions_dict (dict): A dictionary where each key maps to a list of two percentage strings.
                               Example:
                               {
                                   'button': ['50%', '80%'],
                                   'icon': ['25%', '75%']
                               }
        screen_width (int): The width of the screen in pixels.
        screen_height (int): The height of the screen in pixels.

    Returns:
        dict: A dictionary with the same keys, mapping to tuples of (x, y) pixel coordinates.
    """
    converted_positions = {}
    for key, value in positions_dict.items():
        # Ensure that 'value' is a list or tuple with exactly two elements
        if not (isinstance(value, (list, tuple)) and len(value) == 2):
            raise ValueError(f"Value for key '{key}' must be a list or tuple of two percentage strings.")
        
        x_str, y_str = value

        # Ensure that both x_str and y_str are strings ending with '%'
        if not (isinstance(x_str, str) and x_str.endswith('%')):
            raise ValueError(f"x value for key '{key}' must be a string ending with '%'.")
        if not (isinstance(y_str, str) and y_str.endswith('%')):
            raise ValueError(f"y value for key '{key}' must be a string ending with '%'.")
        
        # Convert percentage strings to float values
        x_pct = float(x_str.strip('%'))
        y_pct = float(y_str.strip('%'))

        # Validate percentage ranges
        if not (0 <= x_pct <= 100):
            raise ValueError(f"x percentage for key '{key}' must be between 0% and 100%.")
        if not (0 <= y_pct <= 100):
            raise ValueError(f"y percentage for key '{key}' must be between 0% and 100%.")

        # Convert percentages to pixel coordinates with rounding
        x_px = int(round((x_pct / 100) * screen_width))
        y_px = int(round((y_pct / 100) * screen_height))

        converted_positions[key] = (x_px, y_px)

    return converted_positions
