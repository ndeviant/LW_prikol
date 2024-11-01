# utils/game_utils.py

import logging
import random
import time

from logging_config import status_logger
from .adb_utils import (
    capture_screenshot,
    click_at_location,
    get_current_running_app,
    launch_package,
    swipe_down,
)
from .image_processing import find_icon_on_screen
from .utils import random_sleep
from logging_config import applicant_logger  # For logging applicant acceptances

logger = logging.getLogger(__name__)

def check_game_status(device_id, options, templates):
    """
    Checks if the game and secretary screen are running.
    """
    package_name = options['packageName']
    is_game_running = get_current_running_app(device_id) == package_name
    if is_game_running:
        status_logger.debug(f"Game is running on device {device_id}.")
        screenshot_path = capture_screenshot(device_id)
        template_position = find_icon_on_screen(
            screenshot_path,
            templates['firstLady'],
            threshold=float(options.get('imageMatchThreshold', 0.8)),
        )
        if template_position:
            status_logger.info("Secretary screen is active.")
            return True
        else:
            status_logger.info("Secretary screen is not active.")
    else:
        status_logger.info(f"Game is not running on device {device_id}.")
    return False

def launch_secretary_screen(device_id, options, templates):
    """
    Launches the game and navigates to the secretary screen.
    """
    package_name = options['packageName']
    boot_timer = options.get('bootTimer', 120)

    status_logger.info(f"Launching the game package: {package_name}.")
    launch_package(device_id, package_name)
    time.sleep(boot_timer)
    status_logger.info(f"Waited {boot_timer} seconds for the game to boot.")
    # Additional navigation steps can be added here if needed

def open_position_menu(device_id, secretary_position, button_positions, options):
    """
    Opens the position menu and position list for the given secretary.
    """
    sleep_interval = options['sleep']
    click_at_location(secretary_position[0], secretary_position[1], device_id)
    random_sleep(sleep_interval)
    click_at_location(
        button_positions['list'][0],
        button_positions['list'][1],
        device_id
    )
    random_sleep(sleep_interval)

def close_menu(device_id, button_positions, options):
    """
    Closes the current menu by clicking the close button twice with a delay.
    """
    sleep_interval = options['sleep']
    for _ in range(2):
        click_at_location(
            button_positions['close'][0],
            button_positions['close'][1],
            device_id
        )
        random_sleep(sleep_interval)

def swipe_to_top(device_id, center_x, center_y, swipe_distance, options, times=3):
    """
    Swipes down multiple times to ensure reaching the top of the list.
    """
    sleep_interval = options['sleep']
    for _ in range(times):
        swipe_down(device_id, center_x, center_y, swipe_distance)
        random_sleep(sleep_interval)

def accept_applicants(device_id, templates, options, max_accepts=5):
    """
    Captures and clicks on accept icons up to a maximum count.
    """
    accept_counter = 0
    sleep_interval = options['sleep']
    threshold = float(options['imageMatchThreshold'])

    while accept_counter < max_accepts:
        screenshot_path = capture_screenshot(device_id)
        icon_position = find_icon_on_screen(
            screenshot_path,
            templates['accept'],
            threshold=threshold,
        )
        if icon_position:
            click_at_location(icon_position[0], icon_position[1], device_id)
            accept_counter += 1
            random_sleep(sleep_interval)
            applicant_logger.info(f"Accepted applicant #{accept_counter} at position {icon_position}.")
        else:
            break
    if accept_counter == 0:
        applicant_logger.info("No applicants to accept.")
    return accept_counter

def handle_applicants(device_id, secretary_position, button_positions, options, templates):
    """
    Opens the position menu, checks for applicants, accepts them, and closes the menu.
    """
    sleep_interval = options['sleep']
    threshold = float(options['imageMatchThreshold'])

    applicant_logger.info(f"Handling applicants for secretary at position {secretary_position}.")
    open_position_menu(device_id, secretary_position, button_positions, options)

    # Check if there are any applicants
    initial_screenshot = capture_screenshot(device_id)
    has_applicants = find_icon_on_screen(
        initial_screenshot,
        templates['accept'],
        threshold=threshold,
    )

    if not has_applicants:
        applicant_logger.info("No applicants found for this secretary.")
        close_menu(device_id, button_positions, options)
        return 0

    # Swipe to the top of the list
    screen_width, screen_height = get_screen_size(device_id)
    SWIPE_MULTIPLIER_MIN = 0.75
    SWIPE_MULTIPLIER_MAX = 1.25
    SWIPE_HEIGHT_FACTOR = 0.3
    swipe_distance = random.uniform(
        SWIPE_MULTIPLIER_MIN * (screen_height * SWIPE_HEIGHT_FACTOR),
        SWIPE_MULTIPLIER_MAX * (screen_height * SWIPE_HEIGHT_FACTOR)
    )
    swipe_to_top(
        device_id,
        screen_width // 2,
        screen_height // 2,
        swipe_distance,
        options,
        times=10
    )

    # Process accept icons
    applicants_accepted = accept_applicants(device_id, templates, options)

    # Close position and menu
    close_menu(device_id, button_positions, options)
    applicant_logger.info(f"Finished handling applicants. Total accepted: {applicants_accepted}.")

    return applicants_accepted
