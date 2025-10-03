
import time
from typing import Callable, List, Optional, Tuple
import os
import asyncio

from src.core.config import CONFIG
from src.core.helpers import throttle
from src.core.image_processing import find_templates
from src.core.logging import app_logger
from src.game.device import device

class GameControls():
    _instance: Optional['GameControls'] = None
    _initialized: bool = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        
        self.device = device

    # Delegation methods
    def human_delay(self, *args, **kwargs) -> None:
        """
        Delegates to the human_delay function from the device control strategy.
        """
        return self.device.human_delay(*args, **kwargs)

    def find_template(
        self,
        template_name: str,
        error_msg: Optional[str] = None,
        success_msg: Optional[str] = None,
        critical: bool = False,
        wait: float = None,
        interval: float = None,
        tap: bool = False,
        tap_duration: float = None,
        tap_offset: Tuple[int, int] = (0, 0),
        search_region: Tuple[int, int, int, int] = None,
        file_name_getter: Callable[[str, bool], str] = None,
    ) -> Optional[Tuple[int, int]]:
        """A wrapper function that calls find_templates with all its arguments."""

        # This single line calls the first function with all the arguments it received.
        locations = find_templates(
            template_name=template_name,
            error_msg=error_msg,
            success_msg=success_msg,
            critical=critical,
            wait=wait,
            interval=interval,
            tap=tap,
            tap_duration=tap_duration,
            tap_offset=tap_offset,
            search_region=search_region,
            file_name_getter=file_name_getter,
            # Diff
            find_one=True
        )
        
        return locations[0] if locations else None

    def find_templates(
        self,
        template_name: str,
        error_msg: Optional[str] = None,
        success_msg: Optional[str] = None,
        critical: bool = False,
        wait: float = None,
        interval: float = None,
        tap: bool = False,
        tap_duration: float = None,
        tap_offset: Tuple[int, int] = (0, 0),
        search_region: Tuple[int, int, int, int] = None,
        file_name_getter: Callable[[str, bool], str] = None,
    ) -> Optional[List[Tuple[int, int]]]:
        """A wrapper function that calls find_templates with all its arguments."""

        # This single line calls the first function with all the arguments it received.
        locations = find_templates(
            template_name=template_name,
            error_msg=error_msg,
            success_msg=success_msg,
            critical=critical,
            wait=wait,
            interval=interval,
            tap=tap,
            tap_duration=tap_duration,
            tap_offset=tap_offset,
            search_region=search_region,
            file_name_getter=file_name_getter,
        )
        
        return locations

    # Main
    def launch_game(self) -> bool:
        """Launch the game"""
        if self.device.is_app_running:
            self.device.force_stop_package()
            self.device.human_delay('app_close_wait')

        self.device.launch_package()
        
        start_time = time.time()
        while time.time() - start_time < CONFIG['timings']['launch_max_wait']:
            app_logger.debug("Running launch_game, looking for 'start' and 'home' icons")

            # Check for start button first
            start_loc = self.find_template("start")
            if start_loc:
                app_logger.debug("Found start button, clicking it")
                self.device.click(start_loc[0], start_loc[1])
                self.device.human_delay('menu_animation')
            
            # Check for home icon
            home_loc = self.find_template("home")
            if home_loc:
                app_logger.debug("Found home icon")
                self.device.human_delay('menu_animation')
                self.navigate_home(True)
                return True

            #small delay between checks    
            self.device.human_delay(5)
        
        app_logger.error("Could not find home icon after launch")
        return False
    
    def navigate_home(self, force: bool = False) -> bool:
        """Navigate to home screen"""
        try:
            app_logger.info("Navigating home")

            # Check if already at home
            if not force:
                home_loc = self.find_template("home")
                if home_loc:
                    app_logger.debug("Already at home screen")
                    return True
                
            # Press back until we find home screen
            max_attempts = CONFIG.get('max_home_attempts', 10)
            for attempt in range(max_attempts):
                if self.check_active_on_another_device():
                    app_logger.debug("Failed to navigate home: active on another device")
                    return False

                # Not found, press back and wait
                self.device.press_back()
                self.device.human_delay('menu_animation')

                # Take screenshot and look for home
                quit_loc = self.find_template(
                    "quit",                 
                )
                if not quit_loc:
                    # Not found, press back and wait
                    self.device.human_delay('menu_animation')
                    continue

                app_logger.debug("Found quit button")

                # Press back again to get to home
                while quit_loc:
                    self.device.press_back()
                    self.device.human_delay('menu_animation')
                    quit_loc = self.find_template("quit")
                    app_logger.debug("Going back until 'quit' will not be on the screen")

                # Take screenshot and look for base icon
                self.find_template(
                    "base",
                    tap=True,
                )

                self.human_delay("menu_animation")
                
                return True
                
            app_logger.error("Failed to find home screen after maximum attempts")
            return False
            
        except Exception as e:
            app_logger.error(f"Error navigating home: {e}")
            return False
    
    @throttle(1)
    def check_active_on_another_device(self) -> bool:
        """Find another device popup"""
        try:
            if not self.device.is_app_running:
                return False
            
            app_logger.debug("Checking if account is active on another device")
            # Check if notification is on
            notification = self.find_template(
                "another_device",
                file_name_getter=lambda file_name, success, template_name: 
                    file_name if success else None,
                )

            if not notification:
                return False
        
            total_wait_time = CONFIG['timings']['another_device_wait'] or 300

            app_logger.info(f"Account is active on another device, waiting for {total_wait_time}s")

            # The progress step (20% of the total time)
            step_duration = total_wait_time * 0.20
            remaining_time = total_wait_time

            # Loop to show progress
            for i in range(1, 6): # This will loop 5 times for 20%, 40%, 60%, 80%, 100%
                if not self.device.is_app_running:
                    return True
                self.device.human_delay(step_duration, multiplier=1.0) # Assuming human_delay takes the duration
                remaining_time -= step_duration

                app_logger.info(f"App will be restarted. Time remaining: {remaining_time:.1f}s")
                
            # The full delay is now complete
            self.device.cleanup_temp_files()
            self.device.force_stop_package()

            return True
                
        except Exception as e:
            app_logger.error(f"Error check_active_on_another_device: {e}")
            return False
        
    def verify_game_running(self, on_launch_game: Callable = None) -> bool:
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
                if self.check_active_on_another_device():
                    return False
                
                # Check if game is running first
                if self.device.is_app_running:
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
                if self.launch_game() and on_launch_game:
                    on_launch_game()
                
                # Reset retry count after it hits max to prevent sleep time from growing indefinitely
                if retry_count >= CONFIG['max_home_attempts']:
                    retry_count = 0
                    app_logger.warning("Hit maximum attempts, resetting retry counter")

        except Exception as e:
            app_logger.error(f"Error verifying game status: {e}")
            time.sleep(600)  # Sleep for 10 minutes on error
            return False  # This will trigger another retry through the main loop

controls: GameControls = GameControls()