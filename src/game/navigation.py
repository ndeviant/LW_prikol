import time
import re
from src.core.adb import force_stop_package, launch_package, press_back
from src.core.config import CONFIG
from src.core.device import get_screen_size
from src.core.logging import app_logger
from src.core.image_processing import find_template, wait_for_image
from .controls import human_delay, humanized_tap

def navigate_home(device_id: str, force: bool = False) -> bool:
    """Navigate to home screen and handle notifications
    
    Args:
        device_id: ADB device ID
        
    Returns:
        True if navigation successful, False otherwise
    """
    try:
        if force is not True:   
            # check if we are already on home screen
            home_location = find_template(
                        device_id,
                        "config/templates/home.png",
                        threshold=CONFIG['thresholds']['home_icon']
                    )
            if home_location: 
                return True
    
        start_time = time.time()
        while time.time() - start_time < CONFIG['timings']['max_home_wait']:
            # Check for quit button
            quit_location = find_template(
                device_id,
                "config/templates/quit.png",
                threshold=CONFIG['thresholds']['quit_button']
            )
            
            if quit_location:
                press_back(device_id)
                human_delay(CONFIG['timings']['menu_animation'])
                
                # Verify we reached home screen
                home_location = find_template(
                    device_id,
                    "config/templates/home.png",
                    threshold=CONFIG['thresholds']['home_icon']
                )
                
                if home_location:
                    return True
                
            # No quit button or home icon found, press back and check again
            press_back(device_id)
            human_delay(CONFIG['timings']['menu_animation'])
            
        app_logger.warning("Failed to reach home screen within timeout")
        return False
        
    except Exception as e:
        app_logger.error(f"Error navigating home: {e}")
        return False
    
def launch_game(device_id: str):
    """Launch the game"""
    force_stop_package(device_id, CONFIG['package_name'])
    time.sleep(2)  # Wait for app to fully close
    launch_package(device_id, CONFIG['package_name'])

def open_profile_menu(device_id: str) -> bool:
    """Open the profile menu"""
    try:
        width, height = get_screen_size(device_id)
        profile = CONFIG['ui_elements']['profile']
        profile_x = int(width * float(profile['x'].strip('%')) / 100)
        profile_y = int(height * float(profile['y'].strip('%')) / 100)
        humanized_tap(device_id, profile_x, profile_y)

        # Look for notification indicators
        notification = wait_for_image(
            device_id,
            "config/templates/awesome.png",
            timeout=CONFIG['timings']['menu_animation'],
            threshold=CONFIG['thresholds']['secretary_slot']
        )
        
        if notification:
            humanized_tap(device_id, notification[0], notification[1])
            press_back(device_id)
            human_delay(CONFIG['timings']['menu_animation'])

        return True
    except Exception as e:
        app_logger.error(f"Error opening profile menu: {e}")
        return False

def open_secretary_menu(device_id: str) -> bool:
    """Open the secretary menu"""
    try:
        width, height = get_screen_size(device_id)
        profile = CONFIG['ui_elements']['profile']
        secretary = CONFIG['ui_elements']['secretary_menu']

        # Click secretary menu with randomization
        secretary_x = int(width * float(secretary['x'].strip('%')) / 100)
        secretary_y = int(height * float(secretary['y'].strip('%')) / 100)
        humanized_tap(device_id, secretary_x, secretary_y)
      
        return True
    except Exception as e:
        app_logger.error(f"Error opening secretary menu: {e}")
        return False

