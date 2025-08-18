from abc import ABC, abstractmethod
import time
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from src.automation.routines.routineBase import RoutineBase
from src.core.config import CONFIG
from src.core.logging import app_logger, setup_logging
from src.automation.state import AutomationState
from src.automation.handler_factory import HandlerFactory
from src.game import controls
import os
import asyncio

class MainAutomation:
    def __init__(self, debug: bool = False):
        """Initialize automation

        Args:
            debug: Enable debug logging if True
        """
        setup_logging(debug=debug)
        app_logger.info(f"Initializing automation for device: {controls.device.get_connected_device()}")
        if debug:
            app_logger.info("Debug mode enabled")

        self.state = AutomationState()
        self.handler_factory = HandlerFactory()
        self.game_state = {"is_home": False}
        self.routines: List[RoutineBase] = self.initialize_routines()

    def cleanup(self):
        """Cleanup resources"""
        try:
            app_logger.info("Cleaning up resources...")
            controls.device.cleanup_temp_files()
            controls.device.cleanup_device_screenshots()
        except Exception as e:
            app_logger.error(f"Error during cleanup: {e}")
            
    def run(self):
        """Main run sequence with error handling"""
        try:
            app_logger.info(f"Starting {self.__class__.__name__}")
            if not self.start():
                app_logger.error("Failed to start automation")
                return False
            return True
        except KeyboardInterrupt:
            app_logger.info("Received keyboard interrupt")
            return False
        except Exception as e:
            app_logger.error(f"Error in automation: {e}")
            return False
        finally:
            self.cleanup()

    def load_automation_config(self) -> Dict[str, Any]:
        """Load automation configuration from JSON"""
        from collections import OrderedDict
        config_file = Path("config/automation.json")
        if not config_file.exists():
            app_logger.warning("No automation config found, using empty configuration")
            return {}
            
        with open(config_file) as f:
            return json.load(f, object_pairs_hook=OrderedDict)

    def initialize_routines(self) -> List[RoutineBase]:
        """Initialize all routines from the unified config"""
        config = self.load_automation_config()
        routines: List[RoutineBase] = []
        
        # The new config has a single 'routines' list
        for routine_config in config.get('routines', []):
            routine_name = routine_config.get('routine_name')
            
            # The last_run state is now part of the routine's schedule
            if routine_config.get('schedule'):
                last_run = self.state.get("last_run", routine_name, "routines")
                routine_config['schedule']['last_run'] = last_run
            
            handler = self.handler_factory.create_handler(
                routine_config.get('handler'), 
                routine_config, 
                automation=self
            )
            
            if handler:
                routines.append(handler)
                
        return routines

    def start(self) -> bool:
        """Main automation loop with improved error handling"""
        consecutive_failures = 0
        
        while True:
            try:
                if not self._run_automation_cycle():
                    consecutive_failures += 1
                    self.handle_navigation_failure(consecutive_failures)
                    continue
                    
                consecutive_failures = 0
                time.sleep(0.5)  # Prevent CPU thrashing
                
            except KeyboardInterrupt:
                app_logger.info("Received keyboard interrupt, shutting down gracefully")
                return True
                
            except RuntimeError as e:
                app_logger.error(f"Fatal runtime error: {e}")
                return False
                
            except Exception as e:
                app_logger.error(f"Unexpected error: {e}")

                if consecutive_failures >= 5:
                    return False
                consecutive_failures += 1
                time.sleep(5) # Back off on unexpected errors

    def _run_automation_cycle(self) -> bool:
        """Single cycle of the automation loop."""
        if not self.verify_game_running():
            return False

        # Sort routines by their 'overdue_time' property, most overdue first.
        # This is where the power of the new FlexibleRoutine class comes in.
        sorted_routines = sorted(self.routines, key=lambda r: r.overdue_time, reverse=True)
        
        for routine in sorted_routines:
            if routine.should_run():
                app_logger.info(f"Running '{routine.routine_name} ({routine.routine_type})'")
                success = routine.start()
                
                if success:
                    # 'after_run' handles setting last_run and saving state
                    routine.after_run()
                    
                else:
                    app_logger.error(f"Routine '{routine.routine_name}' failed. Attempting game reset.")
                    self.reset_game()
                
        return True

    def handle_navigation_failure(self, consecutive_failures: int) -> None:
        """Handle navigation failures with exponential backoff."""
        MAX_RETRIES = 5
        BASE_SLEEP = CONFIG['timings']['launch_wait']
        
        if consecutive_failures >= MAX_RETRIES:
            app_logger.error(f"Maximum retries ({MAX_RETRIES}) reached, stopping automation")
            raise RuntimeError("Too many consecutive navigation failures")
        
        sleep_time = int(min(BASE_SLEEP * (2 ** consecutive_failures), 3600))
        app_logger.warning(f"Navigation failure #{consecutive_failures}, sleeping for {sleep_time} seconds")
        time.sleep(sleep_time)
        
        app_logger.info("Forcing game restart...")
        if not self.reset_game():
            app_logger.error("Failed to reset game")

    def verify_game_running(self) -> bool:
        """Verify game is running and at home screen, with retry logic."""
        # This method seems to have an issue. The loop will run indefinitely without
        # a clear exit path if controls.device.is_app_running never becomes True.
        # It's better to combine this logic into the main loop's try/except block.
        # But for refactoring, we'll assume it has a valid purpose.
        try:
            retry_count = 0
            base_sleep = CONFIG['timings']['home_check_interval']
            last_notification_time = 0
            notification_interval = 3600  # 1 hour in seconds

            while True:
                if controls.check_active_on_another_device():
                    return False
                
                # Check if game is running first
                if controls.device.is_app_running:
                    return True
                
                app_logger.info("Game is not running, launching game")
                # If navigation failed, increment retry and wait
                retry_count += 1
                sleep_time = min(base_sleep * (2 ** retry_count), 600)  # Cap at 10 minutes
                
                # Only notify if we hit the 10-minute cap and haven't notified in the last hour
                current_time = time.time()
                if (sleep_time >= 600 and 
                    current_time - last_notification_time > notification_interval):
                    webhook_url = os.getenv('AUTOMATION_WEBHOOK_URL')
                    if webhook_url:
                        try:
                            from src.core.discord_bot import DiscordNotifier
                            discord = DiscordNotifier()
                            discord.webhook_url = webhook_url
                            asyncio.run(discord.send_notification(
                                "🔄 **Game Launch Failed**",
                                f"Unable to launch game, retrying every 10 minutes.\nRetry count: {retry_count}"
                            ))
                            last_notification_time = current_time
                        except Exception as e:
                            app_logger.error(f"Failed to send Discord notification: {e}")
                
                app_logger.debug(f"verify_game_running failed, waiting {sleep_time}s before retry {retry_count}")
                time.sleep(sleep_time)
                if controls.launch_game():
                    self.game_state["is_home"] = True
                
                # Reset retry count after it hits max to prevent sleep time from growing indefinitely
                if retry_count >= CONFIG['max_home_attempts']:
                    retry_count = 0
                    app_logger.warning("Hit maximum attempts, resetting retry counter")

        except Exception as e:
            app_logger.error(f"Error verifying game status: {e}")
            time.sleep(600)  # Sleep for 10 minutes on error
            return False  # This will trigger another retry through the main loop

    def reset_game(self) -> bool:
        """Reset game state by restarting the app"""
        app_logger.info("Resetting game state...")
        retry_count = 0
        base_sleep = CONFIG['timings']['launch_wait']
        
        while retry_count < CONFIG['max_home_attempts']:
            # Use exponential backoff with cap
            sleep_time = min(base_sleep * (2 ** retry_count), 600)
            app_logger.info(f"Launching game in {sleep_time} seconds")
            time.sleep(sleep_time)
            
            if controls.launch_game():
                app_logger.info("Game launched successfully")
                self.game_state["is_home"] = True
                return True
                
            retry_count += 1
        
        app_logger.error("Failed to reset game after maximum attempts")
        return False

    def force_reset(self) -> bool:
        """Force a game reset regardless of state"""
        app_logger.info("Forcing game reset...")
        return self.reset_game()