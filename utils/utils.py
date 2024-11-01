# utils/utils.py

import logging
import random
import time
from datetime import datetime, timedelta

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

def convert_percentage_positions(positions_dict, screen_width, screen_height):
    """
    Converts positions specified as percentages to actual pixel coordinates.
    """
    converted_positions = {}
    for key, value in positions_dict.items():
        x_str, y_str = value
        x = int(float(x_str.strip('%')) / 100 * screen_width)
        y = int(float(y_str.strip('%')) / 100 * screen_height)
        converted_positions[key] = (x, y)
    return converted_positions
