# utils/game_utils.py

import os
import time
import random
import subprocess
from typing import Dict, List, Optional, Tuple
from pathlib import Path

from logging_config import app_logger
from .error_handling import ImageProcessingError, DeviceError
from .game_options import GameOptions
from .config_validation import TemplateConfig, PositionsConfig
from .context import DeviceContext
from .device_utils import get_screen_size
from .image_utils import capture_screenshot, find_all_matches, find_on_screen
from .adb_utils import (
    launch_package,
    force_stop_package,
    press_back,
    humanized_tap,
    swipe_up,
    humanized_swipe
)
from .constants import REQUIRED_SECRETARIES

def parse_percentage(percentage_str: str) -> float:
    """Convert percentage string (e.g. '7.5%') to float (0.075)"""
    return float(percentage_str.strip('%')) / 100

def parse_position(x_percent: str, y_percent: str) -> tuple[int, int]:
    """Convert percentage strings (e.g. '7.5%', '5%') to screen coordinates.
    Coordinates are calculated from top-left (0,0) to bottom-right (width,height)"""
    screen_width, screen_height = DeviceContext.get_screen_dimensions()
    app_logger.debug(f"Screen dimensions from context: {screen_width}x{screen_height}")
    
    x = int(screen_width * parse_percentage(x_percent))
    y = int(screen_height * parse_percentage(y_percent))
    app_logger.debug(f"Calculated position: x={x} ({x_percent} of {screen_width}), y={y} ({y_percent} of {screen_height})")
    
    return (x, y)

def clear_notifications(device_id: str, templates: TemplateConfig, options: GameOptions) -> None:
    """Clear all notifications by pressing back until quit button appears, then one more time"""
    try:
        app_logger.info("Clearing notifications")
        max_attempts = 5  # Maximum number of back presses to try
        
        for attempt in range(max_attempts):
            # Press back with variable delay
            press_back(device_id)
            time.sleep(random.uniform(options.sleep * 1.2, options.sleep * 1.5))
            
            # Check for quit button
            screenshot_path = os.path.join('tmp', f'screen_{int(time.time())}.png')
            capture_screenshot(device_id, filename=screenshot_path)
            
            if 'quit' in templates.buttons:
                matches = find_all_matches(
                    screenshot_path=screenshot_path,
                    template_path=templates.buttons['quit'],
                    threshold=0.8
                )
                if matches:
                    app_logger.info("Found quit button, pressing back one more time")
                    # Extra delay before final back press
                    time.sleep(random.uniform(options.sleep * 1.5, options.sleep * 2))
                    press_back(device_id)
                    # Extra delay after final back
                    time.sleep(random.uniform(options.sleep * 2, options.sleep * 2.5))
                    return
            
            # Clean up screenshot
            if os.path.exists(screenshot_path):
                os.remove(screenshot_path)
                
        app_logger.warning("Quit button not found after max attempts")
        
    except Exception as e:
        app_logger.error(f"Error clearing notifications: {e}")
        raise

def navigate_startup_screens(
    device_id: str,
    templates: TemplateConfig,
    options: GameOptions,
    positions: PositionsConfig
) -> bool:
    """Navigate to the secretary screen using humanized interactions"""
    try:
        # Wait for game to load with timeout
        if not wait_for_game_load(device_id, templates, timeout=120):
            raise ImageProcessingError("Game failed to load within timeout")
        
        # Clear notifications with back button
        clear_notifications(device_id, templates, options)
        
        # Step 1: Click profile button with slight variation
        app_logger.info("Opening profile screen")
        profile_x, profile_y = parse_position(positions.profile.x, positions.profile.y)
        app_logger.debug(f"Clicking profile at ({profile_x}, {profile_y})")
        humanized_tap(device_id, profile_x, profile_y)
        time.sleep(random.uniform(options.sleep * 1.8, options.sleep * 2.2))
        
        # Step 2: Check and clear any likes
        app_logger.info("Checking for likes")
        screenshot_path = os.path.join('tmp', f'screen_{int(time.time())}.png')
        capture_screenshot(device_id, filename=screenshot_path)
        
        if 'awesome' in templates.buttons:
            matches = find_all_matches(
                screenshot_path=screenshot_path,
                template_path=templates.buttons['awesome'],
                threshold=0.8
            )
            if matches:
                app_logger.info("Clearing like notification")
                x, y = matches[0]
                humanized_tap(device_id, x, y)
                time.sleep(random.uniform(options.sleep * 1.5, options.sleep * 2))
        
        # Step 3: Click secretary menu with variation
        app_logger.info("Opening secretary menu")
        menu_x, menu_y = parse_position(positions.secretaryMenu.x, positions.secretaryMenu.y)
        app_logger.debug(f"Clicking secretary menu at ({menu_x}, {menu_y})")
        humanized_tap(device_id, menu_x, menu_y)
        time.sleep(random.uniform(options.sleep * 1.8, options.sleep * 2.2))
        
        # Step 4: Scroll to bottom with variable speed
        app_logger.info("Scrolling to bottom")
        swipe_up(device_id)
        time.sleep(random.uniform(options.sleep * 0.8, options.sleep * 1.2))
        
        return True
        
    except Exception as e:
        app_logger.error(f"Failed to navigate to secretary screen: {e}")
        return False

def test_relaunch(device_id: str, templates: TemplateConfig, options: GameOptions, positions: PositionsConfig) -> bool:
    """Test relaunching the game and navigating to secretary screen"""
    try:
        app_logger.info("Starting relaunch test (1 iterations)")
        
        # Initialize device context
        DeviceContext.initialize(device_id)
        
        # Force close game first
        app_logger.info("Force closing game")
        force_stop_package(device_id, options.package_name)
        time.sleep(options.sleep)
        
        # Launch game and navigate
        app_logger.info("Launching game")
        launch_package(device_id, options.package_name)
        return navigate_startup_screens(device_id, templates, options, positions)
        
    except Exception as e:
        app_logger.error(f"Relaunch test failed: {e}")
        return False

def wait_for_game_load(device_id: str, templates: TemplateConfig, timeout: int = 120) -> bool:
    """Wait for game to load by looking for home icon, with timeout"""
    app_logger.info(f"Waiting up to {timeout} seconds for game to load")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        # Take screenshot
        screenshot_path = os.path.join('tmp', f'screen_{int(time.time())}.png')
        if not capture_screenshot(device_id, filename=screenshot_path):
            continue
        
        # Look for home icon
        home_template = "images/templates/home.png"
        if os.path.exists(home_template):
            matches = find_all_matches(
                screenshot_path=screenshot_path,
                template_path=home_template,
                threshold=0.8
            )
            if matches:
                elapsed = int(time.time() - start_time)
                app_logger.info(f"Game loaded after {elapsed} seconds")
                return True
        else:
            app_logger.error(f"Home template not found at: {home_template}")
            return False
        
        # Clean up screenshot
        if os.path.exists(screenshot_path):
            os.remove(screenshot_path)
            
        # Wait before next check
        time.sleep(3)
    
    app_logger.error(f"Game failed to load after {timeout} seconds")
    return False

def verify_screen_state(device_id: str, templates: TemplateConfig, expected_screen: str = "main") -> bool:
    """Verify current screen state by looking for specific UI elements"""
    try:
        screenshot_path = os.path.join('tmp', f'screen_{int(time.time())}.png')
        capture_screenshot(device_id, filename=screenshot_path)
        
        if expected_screen == "main":
            # Check for list button which should be visible on main screen
            if 'list' in templates.buttons:
                matches = find_all_matches(
                    screenshot_path=screenshot_path,
                    template_path=templates.buttons['list'],
                    threshold=0.8
                )
                if matches:
                    app_logger.debug("Found list button, on main screen")
                    return True
                else:
                    app_logger.debug("List button not found, might be on wrong screen")
                    return False
        
        return False
        
    except Exception as e:
        app_logger.error(f"Error verifying screen state: {e}")
        return False
    finally:
        if os.path.exists(screenshot_path):
            os.remove(screenshot_path)

def verify_and_fix_screen(device_id: str, templates: TemplateConfig, options: GameOptions, max_backs: int = 3) -> bool:
    """Try to get back to main screen if we're stuck"""
    try:
        # First check if we're already on main screen
        if verify_screen_state(device_id, templates):
            return True
            
        # Try pressing back a few times to get to main screen
        for i in range(max_backs):
            press_back(device_id)
            # Longer delay after back press
            time.sleep(random.uniform(options.sleep * 2.5, options.sleep * 3))
            
            if verify_screen_state(device_id, templates):
                # Extra delay after confirming screen state
                time.sleep(random.uniform(options.sleep * 1.5, options.sleep * 2))
                return True
        
        return False
        
    except Exception as e:
        app_logger.error(f"Error fixing screen state: {e}")
        return False

def process_secretaries(
    device_id: str,
    templates: TemplateConfig,
    options: GameOptions,
    positions: PositionsConfig
) -> bool:
    """Process all secretaries in order"""
    try:
        app_logger.info("Starting secretary processing")
        
        # Get list button position
        list_x, list_y = parse_position(positions.list.x, positions.list.y)
        accept_x, accept_y = parse_position(positions.accept.x, positions.accept.y)
        
        # First detect all secretary positions
        secretary_positions = detect_secretary_positions(device_id, templates, options)
        
        # Track secretaries processed for health check
        secretaries_since_check = 0
        
        # Process required secretaries first
        for secretary in REQUIRED_SECRETARIES:
            app_logger.info(f"Processing secretary {secretary}")
            
            if secretary not in secretary_positions:
                app_logger.warning(f"Secretary {secretary} position not found, skipping")
                continue
                
            # Click secretary position
            x, y = secretary_positions[secretary]
            app_logger.debug(f"Clicking secretary {secretary} at ({x}, {y})")
            humanized_tap(device_id, x, y)
            # Longer delay after clicking secretary
            time.sleep(random.uniform(options.sleep * 2.5, options.sleep * 3))
            
            # Perform health check if needed
            if secretaries_since_check >= 3:
                app_logger.info("Performing health check")
                # Take screenshot and verify list button is visible
                screenshot_path = os.path.join('tmp', f'screen_{int(time.time())}.png')
                capture_screenshot(device_id, filename=screenshot_path)
                
                if 'list' in templates.buttons:
                    matches = find_all_matches(
                        screenshot_path=screenshot_path,
                        template_path=templates.buttons['list'],
                        threshold=0.8
                    )
                    if not matches:
                        app_logger.error("Health check failed - list not accessible")
                        return False
                    app_logger.debug("Health check passed - list button found")
                    secretaries_since_check = 0
                
                # Clean up screenshot
                if os.path.exists(screenshot_path):
                    os.remove(screenshot_path)
            
            # Click list button
            app_logger.debug(f"Clicking list at ({list_x}, {list_y})")
            humanized_tap(device_id, list_x, list_y)
            # Longer delay after clicking list
            time.sleep(random.uniform(options.sleep * 2.5, options.sleep * 3))
            
            # Scroll to top of list (3 swipes)
            app_logger.debug("Scrolling to top of list")
            for _ in range(3):
                # Swipe down (reverse of swipe up)
                width, height = DeviceContext.get_screen_dimensions()
                center_x = (width // 2) + random.randint(-30, 30)
                start_y = height // 3
                end_y = start_y + 300
                humanized_swipe(device_id, center_x, start_y, center_x, end_y)
                time.sleep(random.uniform(options.sleep * 0.5, options.sleep * 0.8))
            
            # Process accept buttons
            found_accept = True  # Start true to check first screen
            while found_accept:
                # Take screenshot and look for accept buttons
                screenshot_path = os.path.join('tmp', f'screen_{int(time.time())}.png')
                capture_screenshot(device_id, filename=screenshot_path)
                
                found_accept = False
                if 'accept' in templates.buttons:
                    matches = find_all_matches(
                        screenshot_path=screenshot_path,
                        template_path=templates.buttons['accept'],
                        threshold=0.8
                    )
                    
                    # Filter out duplicate accept buttons and sort by Y position (top to bottom)
                    unique_matches = []
                    for match in matches:
                        x, y = match
                        is_duplicate = False
                        for ux, uy in unique_matches:
                            if abs(x - ux) < 10 and abs(y - uy) < 10:
                                is_duplicate = True
                                break
                        if not is_duplicate:
                            unique_matches.append((x, y))
                    
                    # Sort matches by Y position (top to bottom)
                    unique_matches.sort(key=lambda pos: pos[1])
                    
                    if unique_matches:
                        found_accept = True
                        # Only click the topmost accept button
                        x, y = unique_matches[0]
                        app_logger.info(f"Found accept button at ({x}, {y})")
                        humanized_tap(device_id, x, y)
                        time.sleep(random.uniform(options.sleep * 2.5, options.sleep * 3))
                
                # Clean up screenshot
                if os.path.exists(screenshot_path):
                    os.remove(screenshot_path)
                    
                # If we found an accept on this screen, scroll down for more
                if found_accept:
                    width, height = DeviceContext.get_screen_dimensions()
                    center_x = (width // 2) + random.randint(-30, 30)
                    humanized_swipe(device_id, center_x, height * 0.7, center_x, height * 0.3)
                    time.sleep(random.uniform(options.sleep * 0.5, options.sleep * 0.8))
            
            # Exit list view with single back press
            app_logger.debug("Pressing back button to exit list view")
            press_back(device_id)
            time.sleep(random.uniform(options.sleep * 2.5, options.sleep * 3))
            
            # Exit secretary menu with single back press
            app_logger.debug("Pressing back button to exit secretary menu")
            press_back(device_id)
            time.sleep(random.uniform(options.sleep * 2.5, options.sleep * 3))
            
            # Increment secretaries processed
            secretaries_since_check += 1
            
        return True
        
    except Exception as e:
        app_logger.error(f"Error processing secretaries: {e}")
        return False

def detect_secretary_positions(
    device_id: str,
    templates: TemplateConfig,
    options: GameOptions
) -> Dict[str, Tuple[int, int]]:
    """Detect positions of all secretary icons"""
    try:
        app_logger.info("Starting Secretary Position Detection")
        
        # Take screenshot
        screenshot_path = os.path.join('tmp', f'screen_{int(time.time())}.png')
        if not capture_screenshot(device_id, filename=screenshot_path):
            raise ImageProcessingError("Failed to capture screenshot")
            
        # Initialize results
        positions = {}
        missing_required = set(REQUIRED_SECRETARIES)
        
        # Process each secretary template
        for name, template_path in templates.secretaries.items():
            app_logger.debug(f"Looking for secretary {name}")
            
            # Find matches with high confidence first
            matches = find_all_matches(
                screenshot_path=screenshot_path,
                template_path=template_path,
                threshold=0.8
            )
            
            if matches:
                # Take first match
                x, y = matches[0]
                positions[name] = (x, y)
                app_logger.info(f"Found {name} at ({x}, {y})")
                
                # Remove from missing if required
                if name in missing_required:
                    missing_required.remove(name)
            else:
                app_logger.debug(f"No matches found for {name}")
                
        # Clean up screenshot
        if os.path.exists(screenshot_path):
            os.remove(screenshot_path)
            
        # Check if all required secretaries were found
        if missing_required:
            raise ImageProcessingError(f"Failed to find required secretaries: {missing_required}")
            
        return positions
        
    except Exception as e:
        app_logger.error(f"Secretary detection failed: {e}")
        raise

def run_automation(device_id: str, templates: TemplateConfig, options: GameOptions, positions: PositionsConfig) -> None:
    """Run the automation loop forever with health checks"""
    last_health_check = time.time()
    health_check_interval = 300  # 5 minutes
    
    while True:
        try:
            # Check if we need to do a health check
            current_time = time.time()
            if current_time - last_health_check >= health_check_interval:
                app_logger.info("Performing periodic health check")
                
                # Verify screen state
                if not verify_screen_state(device_id, templates):
                    app_logger.warning("Health check failed, restarting game")
                    if not test_relaunch(device_id, templates, options, positions):
                        app_logger.error("Failed to restart game")
                        time.sleep(options.sleep * 5)  # Wait longer before retry
                        continue
                
                last_health_check = current_time
            
            # Process secretaries
            if not process_secretaries(device_id, templates, options, positions):
                app_logger.warning("Secretary processing failed, attempting restart")
                if not test_relaunch(device_id, templates, options, positions):
                    app_logger.error("Failed to restart game")
                    time.sleep(options.sleep * 5)  # Wait longer before retry
                    continue
            
            # Add random delay between cycles
            delay = random.uniform(options.sleep * 2, options.sleep * 3)
            app_logger.debug(f"Sleeping for {delay:.2f} seconds")
            time.sleep(delay)
            
        except KeyboardInterrupt:
            app_logger.info("Interrupted by user, exiting")
            break
        except Exception as e:
            app_logger.error(f"Error in automation loop: {e}")
            time.sleep(options.sleep * 5)  # Wait before retry