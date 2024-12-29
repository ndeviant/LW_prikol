"""Secretary automation module"""

from src.core.logging import app_logger
from src.core.device import cleanup_temp_files, cleanup_device_screenshots, get_screen_size, take_screenshot
from src.core.config import CONFIG, CONTROL_LIST
from src.core.adb import press_back
from src.core.image_processing import find_all_templates, wait_for_image, find_template
from src.game.navigation import navigate_home
from .controls import human_delay, humanized_long_press, humanized_tap, handle_swipes
from typing import Tuple
from src.core.text_detection import extract_text_from_region, get_text_regions, log_rejected_alliance

def navigate_and_donate(device_id: str):
    """Navigate to the alliance donate menu and donate"""
    # open alliance menu
    alliance_icon = find_template(
        device_id,
        "config/templates/alliance.png",
        threshold=CONFIG['thresholds']['home_icon']
    )
    if alliance_icon is None:
        return False
    humanized_tap(device_id, alliance_icon[0], alliance_icon[1])

    # open donate menu
    alliance_tech_icon = find_template(
        device_id,
        "config/templates/alliance_tech_icon.png",
        threshold=CONFIG['thresholds']['home_icon']
    )
    if alliance_tech_icon is None:
        return False
    humanized_tap(device_id, alliance_tech_icon[0], alliance_tech_icon[1])
    
    # open recommended donate
    recommend_donate = find_template(
        device_id,
        "config/templates/recommended_flag.png",
        threshold=CONFIG['thresholds']['home_icon']
    )
    if recommend_donate is None:
        return False
    humanized_tap(device_id, recommend_donate[0], recommend_donate[1])

    # donate
    donate_button = find_template(
        device_id,
        "config/templates/donate_button.png",
        threshold=CONFIG['thresholds']['home_icon']
    )
    if donate_button is None:
        return False
    
    humanized_long_press(device_id, donate_button[0], donate_button[1], duration=15.0)

def run_alliance_donate(device_id: str):
    """Full secretary automation including initial navigation"""
    try:
        # Start the processing loop
        navigate_home(device_id);
        
        navigate_and_donate(device_id)

        # Navigate back to home
        navigate_home(device_id)
        
    except KeyboardInterrupt:
        app_logger.info("Received keyboard interrupt, cleaning up...")
        cleanup_temp_files()
        cleanup_device_screenshots(device_id)
        app_logger.info("Cleanup complete, exiting...")

