"""Secretary automation module"""

from src.core.logging import app_logger
from src.core.config import CONFIG, CONTROL_LIST
from src.core.adb import press_back
from src.core.image_processing import find_all_templates, wait_for_image, find_template
from src.core.network_sniffing import start_network_capture
from .controls import human_delay, humanized_tap, handle_swipes
from typing import Tuple
from src.core.text_detection import extract_text_from_region, get_text_regions, log_rejected_alliance

def find_accept_buttons(device_id: str) -> list[Tuple[int, int]]:
    """Find all accept buttons on the screen and sort by Y coordinate"""
    matches = find_all_templates(
        device_id,
        "config/templates/accept.png",
        threshold=CONFIG['thresholds']['accept_button']
    )
    # Sort by Y coordinate (top to bottom)
    return sorted(matches, key=lambda x: x[1])

def find_reject_buttons(device_id: str) -> list[Tuple[int, int]]:
    """Find all reject buttons on the screen"""
    return find_all_templates(
        device_id,
        "config/templates/reject.png",
        threshold=CONFIG['thresholds']['accept_button']
    )

def process_secretary_position(device_id: str, name: str) -> bool:
    """Process a single secretary position"""
    try:        
        # Find and click secretary position
        secretary_location = find_template(
            device_id, 
            f"config/templates/{name}.png",
            threshold=CONFIG['thresholds']['secretary_slot']
        )
        
        if not secretary_location:
            app_logger.error(f"Could not find {name} secretary position")
            return True  # Continue with next position
            
        # Click secretary position
        humanized_tap(device_id, secretary_location[0], secretary_location[1], critical=True)
        human_delay(CONFIG['timings']['tap_delay'])
        
        # Find and click list button
        list_location = wait_for_image(
            device_id, 
            "config/templates/list.png",
            timeout=CONFIG['timings']['list_timeout'],
            threshold=CONFIG['thresholds']['list_button']
        )
        
        if not list_location:
            app_logger.error("List button not found")
            return False
        
        # Start network capture before clicking list
        #capture = start_network_capture(device_id)
        capture = None
        
        # Click list button
        humanized_tap(device_id, list_location[0], list_location[1], critical=True)
        
        # Stop capture
        if capture:
            capture.stop()

        # Initial check for any accept buttons
        accept_locations = find_accept_buttons(device_id)

        if accept_locations:
            # Scroll to top of list if we have more than 5 candidates
            if len(accept_locations) > 5:
                handle_swipes(device_id, direction="up")
                human_delay(CONFIG['timings']['settle_time'])
            
            # Process candidates from top down
            processed = 0
            accepted = 0
            while processed < 5:  # Max 5 applicants
                # Re-detect ALL accept buttons after first attempt
                if processed > 0:
                    accept_locations = find_accept_buttons(device_id)
                
                # Break if no accept buttons are found
                if not accept_locations:
                    break
                    
                # Get the topmost accept button
                topmost_accept = accept_locations[0]
                
                # Get regions and extract text separately
                alliance_region, name_region, screenshot = get_text_regions(topmost_accept, device_id)
                alliance_text, original_text = extract_text_from_region(device_id, alliance_region, languages='eng', img=screenshot)

                if (len(CONTROL_LIST['whitelist']['alliance']) > 0):
                    if alliance_text in CONTROL_LIST['whitelist']['alliance']:
                        app_logger.info(f"Accepting candidate with alliance: {alliance_text}")
                        humanized_tap(device_id, topmost_accept[0], topmost_accept[1], critical=True)
                        accepted += 1
                    else:
                        app_logger.info(f"Rejecting candidate with alliance: {alliance_text}")
                        log_rejected_alliance(alliance_text, original_text)
                        reject_locations = find_reject_buttons(device_id)
                        if reject_locations:
                            # Get topmost reject button (sorted by y-coordinate)
                            topmost_reject = min(reject_locations, key=lambda x: x[1])
                            humanized_tap(device_id, topmost_reject[0], topmost_reject[1], critical=True)
                        #input('Press Enter to continue...')
                        confirm_button = find_template(device_id, "config/templates/confirm.png")
                        humanized_tap(device_id, confirm_button[0], confirm_button[1], critical=True)
                else:
                    humanized_tap(device_id, topmost_accept[0], topmost_accept[1], critical=True)
                
                processed += 1
                
            app_logger.info(f"Accepted {accepted} candidates for {name}")
            
        # Exit menus with verification
        if not exit_to_secretary_menu(device_id):
            app_logger.error("Failed to exit to secretary menu")
            return False
            
        return True
        
    except Exception as e:
        app_logger.error(f"Error processing secretary position: {e}")
        # Try to close menus in case of error
        app_logger.info("Attempting to return to secretary menu...")
        if not exit_to_secretary_menu(device_id):
            app_logger.error("Failed to exit to secretary menu after error")
            return False
        return True

def exit_to_secretary_menu(device_id: str) -> bool:
    """Exit back to secretary menu"""
    try:
        # Press back until we see secretary menu header
        max_attempts = 10
        for _ in range(max_attempts):
            if verify_secretary_menu(device_id):
                return True
                
            press_back(device_id)
            human_delay(CONFIG['timings']['menu_animation'])
            
        app_logger.error("Failed to return to secretary menu")
        return False
        
    except Exception as e:
        app_logger.error(f"Error exiting to secretary menu: {e}")
        return False
    
def verify_secretary_menu(device_id: str) -> bool:
    """Verify we're in the secretary menu"""
    return wait_for_image(
        device_id,
        "config/templates/president.png",
        timeout=CONFIG['timings']['menu_animation'],
        threshold=CONFIG['thresholds']['secretary_slot']
    ) is not None

def process_all_secretary_positions(device_id: str) -> bool:
    """Process all secretary positions"""
    secretary_types = ["strategy", "security", "development", "science", "interior"]
    
    for name in secretary_types:
        result = process_secretary_position(device_id, name)
        if not result:
            return False
            
    return True

def run_secretary_loop(device_id: str):
    """Full secretary automation including initial navigation"""
    try:
        # Start the processing loop
        process_all_secretary_positions(device_id)
        
    except KeyboardInterrupt:
        app_logger.info("Received keyboard interrupt, cleaning up...")

