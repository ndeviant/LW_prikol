
import time
from typing import Callable, List, Optional, Tuple

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

controls: GameControls = GameControls()