import os
import random
import time
from abc import ABC, abstractmethod
from typing import List, Optional, Union

import cv2
import numpy as np

from src.core.logging import app_logger
from src.core.config import CONFIG
from src.core.image_processing import find_and_tap_template, find_template

# 1. Strategy Interface
class ControlStrategy(ABC):
    """
    The Strategy Interface declares operations common to all supported versions
    of some algorithm. The Context uses this interface to call the algorithm
    defined by Concrete Strategies.
    """
    @property
    @abstractmethod
    def is_app_running(self) -> str:
        """
        An abstract property that concrete device subclasses must implement.
        Returns the current status of the device (e.g., "online", "offline", "busy").
        """
        pass


    # Template Method: Defines the skeleton of the 'click' operation
    def click(self, x: int, y: int, duration: float = None, critical: bool = False) -> bool:
        """Perform a humanized tap/long press with randomization
        
        Args:
            x: X coordinate
            y: Y coordinate
            duration: Press duration in seconds
            critical: Whether this is a critical press requiring higher precision
        """
        try:
            if (duration == None):
                duration = 0.1

            # Apply position randomization
            radius = CONFIG['randomization']['critical_radius'] if critical else CONFIG['randomization']['normal_radius']
            rand_x = x + random.randint(-radius, radius)
            rand_y = y + random.randint(-radius, radius)
            
            # Convert duration to milliseconds and add slight randomization
            duration_ms = int(duration * 1000 * random.uniform(0.9, 1.1))
            
            # Execute long press
            success = self._perform_click(rand_x, rand_y, duration_ms)
            if success:
                self.human_delay('tap_delay')
                return True
            return False
            
        except Exception as e:
            app_logger.error(f"Error performing humanized long press: {e}")
            return False

    @abstractmethod
    def _perform_click(self, x: int, y: int, duration_ms: int) -> None:
        """
        Abstract hook method: Implemented by concrete strategies to define
        the specific underlying click mechanism and its unique callback.
        """
        pass

    # Template Method: Defines the skeleton of the 'swipe' operation
    def swipe(self, direction: str = "up", num_swipes: int = 1, duration_ms: int = None) -> None:
        """Handle scrolling with swipes"""
        width, height = self.get_screen_size()
        
        swipe_cfg = CONFIG['ui_elements']['swipe']
        variance_pct = float(CONFIG['randomization']['swipe_variance']['position'].strip('%')) / 100
        
        for i in range(num_swipes):
            if direction == "up":
                start_x = int(width * float(swipe_cfg['start_x'].strip('%')) / 100)
                start_y = int(height * float(swipe_cfg['start_y'].strip('%')) / 100)
                end_x = int(width * float(swipe_cfg['end_x'].strip('%')) / 100)
                end_y = int(height * float(swipe_cfg['end_y'].strip('%')) / 100)
            else:  # down
                start_x = int(width * float(swipe_cfg['start_x'].strip('%')) / 100)
                start_y = int(height * float(swipe_cfg['end_y'].strip('%')) / 100)
                end_x = int(width * float(swipe_cfg['end_x'].strip('%')) / 100)
                end_y = int(height * float(swipe_cfg['start_y'].strip('%')) / 100)
            
            # Add slight variance to avoid detection
            start_x += int(width * random.uniform(-variance_pct, variance_pct))
            start_y += int(height * random.uniform(-variance_pct, variance_pct))
            end_x += int(width * random.uniform(-variance_pct, variance_pct))
            end_y += int(height * random.uniform(-variance_pct, variance_pct))
            
            duration = random.randint(
                CONFIG['timings']['swipe_duration']['min'],
                CONFIG['timings']['swipe_duration']['max']
            )

            if (duration_ms is not None):
                duration = random.randint(
                    duration_ms - 50,
                    duration_ms + 50
                )
            
            self._perform_swipe(start_x, start_y, end_x, end_y, duration)
            self.human_delay('scroll_delay')

    @abstractmethod
    def _perform_swipe(self, x: int, y: int, end_x: int, end_y: int, duration: int) -> None:
        """
        Abstract hook method: Implemented by concrete strategies to define
        the specific underlying swipe mechanism and its unique callback.
        """
        pass   

    @abstractmethod
    def type_text(self, text: str) -> None:
        """Types a given string of text."""
        pass

    @abstractmethod
    def get_screen_size(self) -> tuple[int, int]:
        """Returns the screen resolution (width, height)."""
        pass

    @abstractmethod
    def get_device_list(self) -> List[str]:
        """Returns a list of connected device IDs."""
        pass

    @abstractmethod
    def launch_package(self, package_name: str) -> None:
        """Launches a specific application package."""
        pass

    @abstractmethod
    def force_stop_package(self, package_name: str) -> None:
        """Forces a specific application package to stop."""
        pass

    @abstractmethod
    def press_back(self) -> None:
        """Simulates a 'back' button press."""
        pass

    @abstractmethod
    def get_connected_device(self) -> Optional[str]:
        """Returns the ID of the currently connected device, or None if none."""
        pass

    @abstractmethod
    def simulate_shake(self) -> None:
        """Simulates a shake gesture on the device."""
        pass
    
    @abstractmethod
    def take_screenshot(self) -> Optional[np.ndarray]:
        """Take screenshot and pull to local tmp directory"""

    @abstractmethod
    def cleanup_device_screenshots(self) -> None:
        """Clean up screenshots from device"""

    """"""
    """Common functions"""
    """"""
    def human_delay(self, delay: Union[float, str], default: float = 1, multiplier: float = CONFIG.get('sleep_multiplier', 1.0)):
        """
        Add a human-like delay between actions.
        The delay can be a float (seconds) or a string key to CONFIG['timings'].
        """
        actual_delay: float

        if isinstance(delay, str):
            # If delay is a string, look it up in CONFIG['timings']
            try:
                actual_delay = CONFIG['timings'][delay]
            except KeyError:
                app_logger.debug(f"Warning: Named delay '{delay}' not found in CONFIG['timings']. Defaulting to 'default' arg.")
                actual_delay = default # Fallback if the string key is not found
        elif isinstance(delay, (int, float)):
            # If delay is a float or int, use it directly
            actual_delay = float(delay)

        # Apply the sleep multiplier from CONFIG
        final_delay = actual_delay * multiplier
        """Add a human-like delay between actions"""
        time.sleep(final_delay)

    def launch_game(self):
        """Launch the game"""
        if self.is_app_running:
            self.force_stop_package()
            time.sleep(CONFIG['timings']['app_close_wait'])
        self.launch_package()
        
        start_time = time.time()
        while time.time() - start_time < CONFIG['timings']['launch_max_wait']:
            # Check for start button first
            start_loc = find_template("start")
            if start_loc:
                app_logger.debug("Found start button, clicking it")
                self.click(start_loc[0], start_loc[1])
                self.human_delay('menu_animation')
            
            # Check for home icon
            home_loc = find_template("home")
            if home_loc:
                app_logger.debug("Found home icon")
                time.sleep(CONFIG['timings']['launch_wait'])
                return True
            else:
                self.navigate_home(True)

            #small delay between checks    
            self.human_delay(5)
        
        app_logger.error("Could not find home icon after launch")
        return False
    
    def navigate_home(self, force: bool = False) -> bool:
        """Navigate to home screen"""
        try:
            # Check if already at home
            if not force:
                home_loc = find_template("home")
                if home_loc:
                    app_logger.debug("Already at home screen")
                    return True
                
            # Press back until we find home screen
            max_attempts = CONFIG.get('max_home_attempts', 10)
            for attempt in range(max_attempts):
                # Not found, press back and wait
                self.press_back()
                self.human_delay('menu_animation')

                # Take screenshot and look for home
                quit_loc = find_template("quit")
                if quit_loc:
                    app_logger.debug("Found quit button")

                    # Press back again to get to home
                    while quit_loc:
                        self.press_back()
                        self.human_delay('menu_animation')
                        quit_loc = find_template("quit")

                    # Take screenshot and look for base icon
                    find_and_tap_template(
                        "base"
                    )
                    
                    return True
                    
                # Not found, press back and wait
                self.human_delay('menu_animation')
                
            app_logger.error("Failed to find home screen after maximum attempts")
            return False
            
        except Exception as e:
            app_logger.error(f"Error navigating home: {e}")
            return False
              
    def _save_image_to_disk_background(self, image_np: np.ndarray, filepath: str):
        """Helper function to save image to disk, runs in a separate thread."""
        try:
            cv2.imwrite(str(filepath), image_np)
        except Exception as e:
            app_logger.error(f"Error in background saving image to {filepath}: {e}")

    def cleanup_temp_files(self) -> None:
        """Clean up temporary files"""
        return
        try:
            # Remove entire tmp directory and its contents recursively
            tmp_dir = Path("tmp")
            if tmp_dir.exists():
                for item in tmp_dir.iterdir():
                    try:
                        if item.is_file():
                            item.unlink()
                            app_logger.debug(f"Cleaned up temporary file: {item}")
                        elif item.is_dir():
                            shutil.rmtree(item, ignore_errors=True)
                            app_logger.debug(f"Cleaned up temporary directory: {item}")
                    except Exception as e:
                        app_logger.warning(f"Failed to delete {item}: {e}")
                
                try:
                    tmp_dir.rmdir()
                    app_logger.debug("Cleaned up main temporary directory")
                except Exception as e:
                    app_logger.warning(f"Failed to delete tmp directory: {e}")
        except Exception as e:
            app_logger.error(f"Error cleaning temporary files: {e}")



