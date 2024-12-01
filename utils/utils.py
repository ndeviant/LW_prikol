# utils/utils.py

import logging
import random
import time
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Union
from functools import wraps
from logging_config import app_logger

logger = logging.getLogger(__name__)

def random_sleep(base_interval: float = 1.0, variation: float = 0.5):
    """
    Sleeps for a random amount of time around the base interval.
    
    Args:
        base_interval (float): Base time to sleep in seconds (default: 1.0)
        variation (float): Maximum variation in seconds (default: 0.5)
    """
    sleep_duration = random.uniform(
        max(0, base_interval - variation),
        base_interval + variation
    )
    app_logger.debug(f"Sleeping for {sleep_duration:.2f} seconds.")
    time.sleep(sleep_duration)

def get_timestamp():
    """
    Returns the current timestamp as a formatted string.
    """
    return datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")

def check_time_passed(
    last_check: Optional[datetime],
    minutes: Union[int, float]
) -> Tuple[bool, datetime]:
    """
    Check if specified minutes have passed since last check.
    
    Args:
        last_check: Previous check timestamp or None
        minutes: Minutes to wait between checks
        
    Returns:
        Tuple of (should_check: bool, current_time: datetime)
    """
    current_time = datetime.now()
    if last_check is None or current_time - last_check > timedelta(minutes=minutes):
        return True, current_time
    return False, last_check

def convert_percentage_positions(positions_dict, screen_width, screen_height):
    """
    Converts positions specified as percentage strings to actual pixel coordinates.
    """
    converted_positions = {}
    app_logger.debug(f"Converting positions with screen size: {screen_width}x{screen_height}")
    
    for key, value in positions_dict.items():
        try:
            x_str, y_str = value
            x_pct = float(x_str.strip('%'))
            y_pct = float(y_str.strip('%'))
            
            x_px = int((x_pct / 100) * screen_width)
            y_px = int((y_pct / 100) * screen_height)
            
            converted_positions[key] = (x_px, y_px)
            app_logger.debug(f"Converted {key}: from ({x_str}, {y_str}) to ({x_px}, {y_px})")
        except Exception as e:
            app_logger.error(f"Failed to convert position for {key}: {e}")
            raise
    
    return converted_positions

def retry(max_attempts: int = 3, delay: float = 1.0):
    """Decorator for retrying failed operations"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    app_logger.warning(
                        f"Attempt {attempt + 1}/{max_attempts} failed: {e}"
                    )
                    if attempt < max_attempts - 1:
                        time.sleep(delay)
            raise last_exception
        return wrapper
    return decorator

# Usage:
@retry(max_attempts=3)
def find_on_screen(screenshot_path, icon_path, threshold=0.8):
    # Existing implementation
    pass
