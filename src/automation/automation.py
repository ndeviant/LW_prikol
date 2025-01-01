from abc import ABC, abstractmethod
import time
import json
from pathlib import Path
from typing import Dict, Any, Optional
from src.automation.routines.routineBase import RoutineBase
from src.core.config import CONFIG
from src.core.image_processing import find_template
from src.core.logging import app_logger
from src.core.scheduling import update_interval_check, update_schedule
from src.core.adb import get_current_running_app
from src.core.device import cleanup_temp_files, cleanup_device_screenshots
from src.automation.state import AutomationState
from src.automation.handler_factory import HandlerFactory
from src.game.controls import launch_game, navigate_home

class MainAutomation:
    def __init__(self, device_id: str):
        self.device_id = device_id
        self.state = AutomationState()
        config = self.load_automation_config()
        self.time_checks = self.initialize_time_checks(config.get('time_checks', {}))
        self.scheduled_events = self.initialize_scheduled_events(config.get('scheduled_events', {}))
        self.handlers = {}
        self.handler_factory = HandlerFactory()
        
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
            last_run = self.state.get_last_run(check_name, "time_checks")
            checks[check_name] = OrderedDict({
                "last_run": last_run,
                "time_to_check": check_data["interval"],
                "handler": check_data["handler"],
                "needs_check": True  # Force initial check
            })
        return checks

    def initialize_scheduled_events(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize scheduled events from config and saved state"""
        events = {}
        for event_name, event_data in config.items():
            events[event_name] = {
                "last_run": self.state.get_last_run(event_name, "scheduled_events"),
                "day": event_data["schedule"]["day"],
                "time": event_data["schedule"]["time"],
                "handler": event_data["handler"]
            }
        return events

    def get_handler(self, handler_path: str, config: Dict[str, Any] = None) -> Optional[RoutineBase]:
        """Get or create a handler instance"""
        if handler_path not in self.handlers:
            handler = self.handler_factory.create_handler(handler_path, self.device_id, config or {})
            if handler:
                self.handlers[handler_path] = handler
                
        return self.handlers.get(handler_path)

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
        
        # Force game restart
        app_logger.info("Forcing game restart...")
        handler = self.get_handler("src.automation.routines.reset.ResetRoutine", {"interval": 0})
        if handler:
            handler.start()

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

    def run_scheduled_tasks(self):
        current_time = time.time()
        
        # Run time-based checks in config order
        ordered_checks = self.get_ordered_check_names()
        for check_name in ordered_checks:
            check_data = self.time_checks.get(check_name)
            if check_data and self.needs_check(check_name):
                handler = self.get_handler(check_data["handler"], check_data)
                if not handler:
                    # Handler failed to create, mark as not needing check
                    check_data["needs_check"] = False
                    continue
                    
                if handler.should_run():
                    app_logger.info(f"Running {check_name} routine")
                    success = handler.start()
                    
                    if success:
                        handler.after_run()
                        check_data["last_run"] = current_time
                        check_data["needs_check"] = False
                        self.state.set_last_run(check_name, current_time, "time_checks")
                        self.state.save()
                    else:
                        check_data["needs_check"] = False
                    
        # Run scheduled events
        for event_name, event_data in self.scheduled_events.items():
            if self.needs_check(event_name):
                handler = self.get_handler(event_data["handler"], event_data)
                if not handler:
                    # Handler failed to create, mark as not needing check
                    event_data["needs_check"] = False
                    continue
                    
                app_logger.info(f"Running {event_name} event")
                success = handler.start()
                
                if success:
                    handler.after_run()
                    event_data["last_run"] = current_time
                    event_data["needs_check"] = False
                    self.state.set_last_run(event_name, current_time, "scheduled_events")
                    self.state.save()
                else:
                    event_data["needs_check"] = False

    def verify_game_running(self) -> bool:
        """Verify game is running and at home screen, with retry logic"""
        try:
            retry_count = 0
            base_sleep = CONFIG['timings']['home_check_interval']
            
            while retry_count < CONFIG['max_home_attempts']:
                # Check if game is running first
                current_app = get_current_running_app(self.device_id)
                if current_app != CONFIG['package_name']:
                    app_logger.info("Game not running, launching...")
                    launch_game(self.device_id)
                    time.sleep(CONFIG['timings']['launch_wait'])
                
                # Try to navigate home
                if navigate_home(self.device_id):
                    return True
                    
                # If navigation failed, increment retry and wait
                retry_count += 1
                sleep_time = base_sleep * (2 ** retry_count)
                app_logger.debug(f"Navigation failed, waiting {sleep_time}s before retry {retry_count}")
                time.sleep(sleep_time)
                
            app_logger.error("Failed to verify game is running after maximum attempts")
            return False
            
        except Exception as e:
            app_logger.error(f"Error verifying game status: {e}")
            return False

    def needs_check(self, check_name: str) -> bool:
        """Check if a scheduled task needs to be run
        
        Args:
            check_name: Name of the check to verify
            
        Returns:
            True if check exists and needs to be run, False otherwise
        """
        return check_name in self.time_checks and self.time_checks[check_name] and self.time_checks[check_name]['needs_check']