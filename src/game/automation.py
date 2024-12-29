"""Secretary automation module"""

import time
import random
import traceback
from src.core.adb import force_stop_package, get_current_running_app
from src.core.logging import app_logger
from src.core.device import cleanup_temp_files, cleanup_device_screenshots
from src.core.config import CONFIG
from src.core.image_processing import find_template, wait_for_image
from src.game.alliance_donate import run_alliance_donate
from src.game.navigation import launch_game, navigate_home, open_profile_menu, open_secretary_menu
from src.game.secretary_automation import process_all_secretary_positions
from .controls import human_delay, humanized_tap
from src.core.scheduling import update_interval_check, update_schedule
from config.schedule import time_checks as time_check_defaults, scheduled_events as scheduled_events_defaults



def run_automation(device_id: str):
    """Main automation loop
    
    Args:
        device_id: ADB device ID
    """
    try:
        time_checks = time_check_defaults.copy()
        scheduled_events = scheduled_events_defaults.copy()
        app_logger.info("Starting automation loop")
      
        while True:
            try:
                current_time = time.time()
                time_checks = update_interval_check(time_checks, current_time)
                scheduled_events = update_schedule(scheduled_events, current_time)

                # Check if the game is running
                if get_current_running_app(device_id) != CONFIG['package_name'] or time_checks['reset']['needs_check']:
                    app_logger.info("Resetting game...")
                    launch_game(device_id)
                    wait_for_image(device_id, "config/templates/home.png")
                    time_checks['reset']["last_check"] = current_time
                    time_checks['reset']['needs_check'] = False

                # Periodic cleanup
                if time_checks['cleanup']['needs_check']:
                    app_logger.info("Running periodic cleanup...")
                    cleanup_temp_files()
                    cleanup_device_screenshots(device_id)
                    time_checks['cleanup']["last_check"] = current_time
                    time_checks['cleanup']['needs_check'] = False
                
                # Navigate home
                navigate_home(device_id, force=True)

                # Take screenshot and check for help template
                help_location = find_template(device_id, "config/templates/help.png")
                if help_location:
                    app_logger.info("Helping allies!")
                    humanized_tap(device_id, help_location[0], help_location[1])

                # Check if we need to donate
                if time_checks['donate']['needs_check']:
                    app_logger.info("Donating to alliance tech!")
                    run_alliance_donate(device_id)
                    time_checks['donate']["last_check"] = current_time
                    time_checks['donate']['needs_check'] = False

                # Check if we need to run a scheduled event
                if scheduled_events['test_event']['needs_check']:
                    app_logger.info("Running scheduled event: vs_capture")
                    # TODO: Implement vs_capture logic
                    scheduled_events['test_event']["last_check"] = current_time
                    scheduled_events['test_event']['needs_check'] = False

                # navigate back to secretary menu
                app_logger.info("Processing secretary positions")
                open_profile_menu(device_id)
                open_secretary_menu(device_id)
                process_all_secretary_positions(device_id)
                
            except Exception as e:
                app_logger.error(f"Error in main loop: {str(e)}")
                traceback.print_exc()
                human_delay(CONFIG['timings']['error_delay'])
                force_stop_package(device_id, CONFIG['package_name'])
                
    except KeyboardInterrupt:
        app_logger.info("Received keyboard interrupt, cleaning up...")
        cleanup_temp_files()
        cleanup_device_screenshots(device_id)
        app_logger.info("Cleanup complete, exiting...")

