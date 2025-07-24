from abc import ABC, abstractmethod
import time
import json
from pathlib import Path
from typing import Dict, Any, Optional
from src.automation.routines.routineBase import RoutineBase
from src.core.config import CONFIG
from src.core.logging import app_logger, setup_logging
from src.core.scheduling import update_interval_check, update_schedule
from src.core.device import cleanup_temp_files, cleanup_device_screenshots
from src.automation.state import AutomationState
from src.automation.handler_factory import HandlerFactory
from src.game import controls
import os
import asyncio

class MainAutomation:
    def __init__(self, device_id: str, debug: bool = False):
        """Initialize automation
        
        Args:
            device_id: Device identifier
            debug: Enable debug logging if True
        """
        setup_logging(debug=debug)  # Set logging level based on debug flag
        self.device_id = device_id
        app_logger.info(f"Initializing automation for device: {device_id}")
        if debug:
            app_logger.info("Debug mode enabled")
        self.state = AutomationState()
        config = self.load_automation_config()
        self.time_checks = self.initialize_time_checks(config.get('time_checks', {}))
        self.scheduled_events = self.initialize_scheduled_events(config.get('scheduled_events', {}))
        self.handlers = {}
        self.handler_factory = HandlerFactory()
        self.game_state = {"is_home": False}
        
    def cleanup(self):
        """Cleanup resources"""
        try:
            app_logger.info("Cleaning up resources...")
            cleanup_temp_files()
            cleanup_device_screenshots(self.device_id)
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

    def initialize_time_checks(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize time checks from config and saved state"""
        from collections import OrderedDict
        checks = OrderedDict()
        
        # Use config order, not state order
        for check_name, check_data in config.items():
            # Skip if interval is null
            if check_data.get("interval") is None:
                continue
            
            last_run = self.state.get("last_run", check_name, "time_checks")
            checks[check_name] = {
                "last_run": last_run,
                "time_to_check": check_data["interval"],
                "handler": check_data["handler"],
                "needs_check": True,
                "options": check_data.get("options")
            }
        return checks

    def initialize_scheduled_events(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize scheduled events from config and saved state"""
        events = {}
        for event_name, event_data in config.items():
            # Skip if day is null
            if event_data["schedule"]["day"] is None:
                continue
            
            events[event_name] = {
                "last_run": self.state.get("last_run", event_name, "scheduled_events"),
                "last_check": self.state.get("last_check", event_name, "scheduled_events"),
                "day": event_data["schedule"]["day"],
                "time": event_data["schedule"]["time"],
                "handler": event_data["handler"],
                "options": event_data.get("options")
            }
        return events

    def get_handler(self, routine_type: str, routine_name: str, config: Dict[str, Any] = None) -> Optional[RoutineBase]:
        """Get or create a handler instance"""
        if routine_name not in self.handlers:
            handler = self.handler_factory.create_handler(
                config.get("handler"), 
                self.device_id, 
                config or {},
                automation=self  # Pass self reference to the handler
            )
            if handler:
                self.handlers[routine_name] = handler
                
        return self.handlers.get(routine_name)

    def handle_navigation_failure(self, consecutive_failures: int) -> None:
        """Handle navigation failures with exponential backoff"""
        MAX_RETRIES = 5
        BASE_SLEEP = CONFIG['timings']['launch_wait']
        
        if consecutive_failures >= MAX_RETRIES:
            app_logger.error(f"Maximum retries ({MAX_RETRIES}) reached, stopping automation")
            raise RuntimeError("Too many consecutive navigation failures")
        
        sleep_time = int(min(BASE_SLEEP * (2 ** consecutive_failures), 3600))  # Cap at 1 hour
        app_logger.warning(f"Navigation failure #{consecutive_failures}, sleeping for {sleep_time} seconds")
        time.sleep(sleep_time)
        
        # Force game restart using internal reset
        app_logger.info("Forcing game restart...")
        if not self.reset_game():
            app_logger.error("Failed to reset game")

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
                time.sleep(1)  # Prevent CPU thrashing
                
            except KeyboardInterrupt:
                app_logger.info("Received keyboard interrupt, shutting down gracefully")
                return True
                
            except RuntimeError as e:
                app_logger.error(f"Fatal runtime error: {e}")
                return False
                
            except Exception as e:
                app_logger.error(f"Unexpected error: {e}")
                current_tb = e.__traceback__
                while current_tb:
                    print(f"  Frame: {current_tb.tb_frame}")
                    print(f"  Line no: {current_tb.tb_lineno}")
                    print(f"  Filename: {current_tb.tb_frame.f_code.co_filename}")
                    print(f"  Function: {current_tb.tb_frame.f_code.co_name}")
                    print(f"  Local variables: {current_tb.tb_frame.f_locals}")
                    print("-" * 20)
                    current_tb = current_tb.tb_next

                if consecutive_failures >= 5:
                    return False
                consecutive_failures += 1
                time.sleep(5)  # Back off on unexpected errors

    def _run_automation_cycle(self) -> bool:
        """Single cycle of the automation loop"""
        # Update timers
        self.time_checks = update_interval_check(self.time_checks, time.time())
        self.scheduled_events = update_schedule(self.scheduled_events, time.time())

        # Ensure game is running
        if not self.verify_game_running():
            return False

        # Run scheduled tasks
        self.run_scheduled_tasks()
        return True

    def resume(self) -> bool:
        return self.start()
    
    def get_ordered_check_names(self) -> list[str]:
        """Get check names in order from config"""
        config = self.load_automation_config()
        return list(config.get("time_checks", {}).keys())

    def get_ordered_tasks(self) -> list[tuple[str, float, str]]:
        """Get all tasks ordered by how overdue they are"""
        current_time = time.time()
        tasks = []
        
        # Add time-based checks
        for check_name, check_data in self.time_checks.items():
            if not check_data.get('needs_check', True):  # Default to True if missing
                continue
            
            last_run = check_data.get('last_run') or 0
            interval = check_data.get('time_to_check', 0)
            overdue_time = current_time - (last_run + interval)
            tasks.append((check_name, overdue_time, 'time_checks'))
        
        # Add scheduled events
        for event_name, event_data in self.scheduled_events.items():
            if not event_data.get('needs_check', True):  # Default to True if missing
                continue
            tasks.append((event_name, float('inf'), 'scheduled_events'))
        
        # Sort by overdue time (most overdue first)
        return sorted(tasks, key=lambda x: x[1], reverse=True)

    def run_scheduled_tasks(self):
        """Run tasks in order of priority"""
        current_time = time.time()
        ordered_tasks = self.get_ordered_tasks()
        
        for task_name, _, task_type in ordered_tasks:
            if task_type == 'time_checks':
                check_data = self.time_checks[task_name]
                handler = self.get_handler(task_type, task_name, check_data)
            else:  # scheduled_events
                event_data = self.scheduled_events[task_name]
                handler = self.get_handler(task_type, task_name, event_data)

            if not handler:
                continue
                
            if handler.should_run():
                app_logger.info(f"Running {task_name} ({task_type})")
                success = handler.start()
                
                if not success:
                    app_logger.error(f"Task {task_name} failed, attempting game reset")
                    if self.reset_game():
                        # Retry the task after reset
                        success = handler.start()
                
                if success:
                    handler.after_run()
                    if task_type == 'time_checks':
                        check_data["last_run"] = current_time
                        check_data["needs_check"] = False
                    else:
                        event_data["last_run"] = current_time
                        event_data["needs_check"] = False
                        
                    self.state.set("last_run", current_time, task_name, task_type)
                    self.state.save()
                else:
                    if task_type == 'time_checks':
                        check_data["needs_check"] = False
                    else:
                        event_data["needs_check"] = False

    def verify_game_running(self) -> bool:
        """Verify game is running and at home screen, with retry logic"""
        try:
            retry_count = 0
            base_sleep = CONFIG['timings']['home_check_interval']
            last_notification_time = 0
            notification_interval = 3600  # 1 hour in seconds

            while True:
   
                controls.check_active_on_another_device()

                # Check if game is running first
                if controls.is_app_running:
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
                    if webhook_url:  # Only attempt notification if webhook is configured
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
                
                app_logger.debug(f"Navigation failed, waiting {sleep_time}s before retry {retry_count}")
                time.sleep(sleep_time)
                controls.launch_game()
                
                # Reset retry count after it hits max to prevent sleep time from growing indefinitely
                if retry_count >= CONFIG['max_home_attempts']:
                    retry_count = 0
                    app_logger.warning("Hit maximum attempts, resetting retry counter")
            
        except Exception as e:
            app_logger.error(f"Error verifying game status: {e}")
            time.sleep(600)  # Sleep for 10 minutes on error
            return False  # This will trigger another retry through the main loop

    def needs_check(self, check_name: str) -> bool:
        """Check if a scheduled task needs to be run
        
        Args:
            check_name: Name of the check to verify
            
        Returns:
            True if check exists and needs to be run, False otherwise
        """
        return check_name in self.time_checks and self.time_checks[check_name] and self.time_checks[check_name]['needs_check']

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
                if controls.navigate_home(force=True):
                    self.game_state["is_home"] = True
                    return True
                
            retry_count += 1
        
        app_logger.error("Failed to reset game after maximum attempts")
        return False

    def force_reset(self) -> bool:
        """Force a game reset regardless of state"""
        app_logger.info("Forcing game reset...")
        return self.reset_game()