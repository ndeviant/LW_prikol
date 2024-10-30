import time
from utils.adb_utils import capture_screenshot
from utils.image_processing import find_icon_on_screen
from utils.adb_utils import (
    capture_screenshot,
    click_at_location,
    swipe_down,
)
from utils.utils import random_sleep


def open_position_menu(device_id, secretary_position, button_positions, sleep_interval):
    """Opens the position menu and position list for the given secretary."""
    click_at_location(secretary_position[0], secretary_position[1], device_id)
    random_sleep(sleep_interval)
    click_at_location(button_positions['list'][0], button_positions['list'][1], device_id)
    random_sleep(sleep_interval)

def close_position_menu(device_id, button_positions, sleep_interval):
    """Closes the position menu and position list."""
    click_at_location(button_positions['close'][0], button_positions['close'][1], device_id)
    random_sleep(sleep_interval)
    click_at_location(button_positions['close'][0], button_positions['close'][1], device_id)
    random_sleep(sleep_interval)

def swipe_to_top(device_id, center_x, center_y, swipe_distance, sleep_interval, times=3):
    """Swipes down multiple times to ensure reaching the top of the list."""
    for _ in range(times):
        swipe_down(device_id, center_x, center_y, swipe_distance)
        random_sleep(1, 0.4)

def is_home_screen(device_id, target_icon, threshold=0.75, debug=False):
    """
    Checks if the home screen is displayed by detecting the mail icon, and presses the back button
    until the mail icon is found or a max number of attempts is reached.
    
    Args:
        device_id (str): The ID of the device.
        config (dict): Configuration dictionary containing icon paths.
        max_attempts (int): The maximum number of back presses to attempt. Default is 10.
        delay (int): Delay in seconds between each check. Default is 2 seconds.
        threshold (float): Confidence threshold for template matching. Default is 0.8.
        debug (bool): If True, enables debug mode for more output. Default is False.
    
    Returns:
        bool: True if the mail icon is found (indicating the home screen), False if not found after max_attempts.
    """

    # Capture the current screen
    screenshot_path = capture_screenshot(device_id)

    print(screenshot_path)

    # Check if the mail icon is present on the screen
    if find_icon_on_screen(screenshot_path, target_icon, threshold=threshold, debug=debug):
        return True  # Mail icon found, home screen detected
    
    return False  # Mail icon not found after max_attempts