import json
import subprocess
from typing import Any, List, Optional, Union
import time
import os
import re
import traceback
import cv2
import numpy as np
import pywinauto
from pywinauto import Desktop, Application, findwindows 
from pywinauto.keyboard import send_keys
import pyautogui # For simpler mouse/keyboard actions not directly covered by pywinauto's element methods
import concurrent.futures

from src.core.config import CONFIG
from src.core.helpers import ensure_dir
from src.core.logging import app_logger

from .strategy import ControlStrategy

file_save_executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)

# 2. Concrete Strategies

class WindowsControls(ControlStrategy):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.device_id = os.getlogin()
        self.app_name = CONFIG['windows']['app_name']
        self.executable_path = CONFIG['windows']['executable_path']
        self.process_name = CONFIG['windows']['process_name']
        self.backend = CONFIG['windows'].get('backend', "win32") # Use 'uia' for modern apps, 'win32' for older ones
        self.pid: int = None

        self.app = None # pywinauto.Application instance
        self.main_window = None # pywinauto.WindowSpecification or Wrapper object for the main app window
        self.desktop = Desktop(backend=self.backend) 

        # Attempt to connect to the LastWar application immediately
        self._connect_to_lastwar_app()
        app_logger.info(f"[Windows] Initialized WindowsControls for '{self.device_id}'. App connection status: {'Connected' if self.app and self.main_window else 'Failed'}")

    def _connect_to_lastwar_app(self) -> bool:
        """Helper to connect to the LastWar application and get its main window."""

        if not (self.app_name or self.executable_path or self.process_name):
            app_logger.error("[Windows] No application identifier (name, path, or process name) configured for LastWar.")
            return False

        try:
            # Prioritize connecting by process name or path for robustness
            if self.process_name:
                app_logger.debug(f"[Windows] Attempting to connect to LastWar by process name: {self.process_name}")
                # Find PID first using psutil for reliability
                import psutil # Ensure psutil is installed
                pid = None
                for proc in psutil.process_iter(['pid', 'name']):
                    if proc.info['name'].lower() == self.process_name.lower():
                        pid = proc.info['pid']
                        break
                if pid:
                    self.pid = pid
                    self.app = Application(backend=self.backend).connect(process=pid, timeout=10)
                else:
                    app_logger.warning(f"[Windows] Process '{self.process_name}' not found. Cannot connect.")
                    return False
            elif self.executable_path:
                app_logger.debug(f"[Windows] Attempting to connect to LastWar by path: {self.executable_path}")
                self.app = Application(backend=self.backend).connect(path=self.executable_path, timeout=10)
            elif self.app_name:
                app_logger.debug(f"[Windows] Attempting to connect to LastWar by title_re: .*{re.escape(self.app_name)}.*")
                self.app = Application(backend=self.backend).connect(title_re=f".*{re.escape(self.app_name)}.*", timeout=10)
            else:
                app_logger.error("[Windows] No valid connection criteria for LastWar app.")
                return False

            # Get the main window of the connected application
            # Use wait_until_passes to ensure the window is ready
            self.main_window = self.app.top_window() # This gets the WindowSpecification
            self.main_window.wait('ready', timeout=5) # Wait for the window to be ready (visible, enabled)
            self.main_window.set_focus()
            
            app_logger.info(f"[Windows] Successfully connected to LastWar app: '{self.main_window.window_text()}' (PID: {self.app.process})")
            return True
        except pywinauto.timings.TimeoutError:
            app_logger.error(f"[Windows] Timeout connecting to LastWar app using criteria. Is it running and responsive?")
            self.app = None
            self.main_window = None
            return False
        except findwindows.ElementNotFoundError:
            app_logger.error(f"[Windows] LastWar app not found with specified criteria. Please check CONFIG and ensure app is running.")
            self.app = None
            self.main_window = None
            return False
        except findwindows.ElementAmbiguousError as e:
            app_logger.error(f"[Windows] Multiple LastWar app windows found. Please refine criteria in CONFIG. Details: {e}")
            self.app = None
            self.main_window = None
            return False
        except Exception as e:
            app_logger.error(f"[Windows] Unexpected error connecting to LastWar app: {e}")
            app_logger.debug(f"Full error details: {traceback.format_exc()}")
            self.app = None
            self.main_window = None
            return False

    @property
    def is_app_running(self) -> bool:
        """Check if the target LastWar application is running and connected."""
        if self.app and self.app.is_process_running():
            try:
                # Try to refresh the window reference to ensure it's still valid
                self.main_window.wrapper_object() # Accessing wrapper_object can re-validate
                app_logger.debug(f"[Windows] LastWar app is running and connected.")
                return True
            except Exception:
                app_logger.debug("[Windows] LastWar app process is running, but window reference is stale.")
                return False
        app_logger.debug("[Windows] LastWar app process is not running.")
        return False

    def _perform_click(self, x: int, y: int, duration_ms: int = 0) -> bool:
        """Execute a click/long press at coordinates using pyautogui."""
        try:
            pyautogui.moveTo(x, y) # Move mouse to coordinates
            if duration_ms == 0: # Treat 0ms as a simple click
                pyautogui.click()
                app_logger.debug(f"[Windows] Performed click at ({x}, {y})")
            else:
                pyautogui.mouseDown(x=x, y=y) # Mouse down
                time.sleep(duration_ms / 1000.0) # Convert ms to seconds for sleep
                pyautogui.mouseUp(x=x, y=y) # Mouse up
                app_logger.debug(f"[Windows] Performed long press at ({x}, {y}) for {duration_ms}ms")
            return True
        except Exception as e:
            app_logger.error(f"[Windows] Failed to perform click/long press at ({x}, {y}): {e}")
            app_logger.debug(f"Full error details: {traceback.format_exc()}")
            return False

    def _perform_swipe(self, start_x: int, start_y: int, end_x: int, end_y: int, duration_ms: int = 300) -> bool:
        """Swipe screen from start to end coordinates using pyautogui."""
        try:
            pyautogui.moveTo(start_x, start_y)
            pyautogui.mouseDown()
            pyautogui.dragTo(end_x, end_y, duration=duration_ms / 1000.0, mouseDownUp=False) # pyautogui duration is in seconds
            # Hold the mouse button down for an additional 100ms at the end point
            self.human_delay(0.078)
            pyautogui.mouseUp()
            app_logger.debug(f"[Windows] Swiped from ({start_x}, {start_y}) to ({end_x}, {end_y}) for {duration_ms}ms")
            return True

        except Exception as e:
            app_logger.error(f"[Windows] Error swiping screen: {e}")
            app_logger.debug(f"Full error details: {traceback.format_exc()}")
            return False

    def press_back(self) -> bool:
        """Simulate 'Escape' on the LastWar app window."""
        if not self.main_window:
            app_logger.error("[Windows] Cannot press back: LastWar app window not connected.")
            return False
        try:
            self.main_window.set_focus() # Ensure window is focused to receive key input
            send_keys("{ESC}")
            app_logger.debug("[Windows] Pressed back button (ESC) on LastWar window.")
            return True
        except Exception as e:
            app_logger.error(f"[Windows] Error pressing back: {e}")
            app_logger.debug(f"Full error details: {traceback.format_exc()}")
            return False
            
    def simulate_shake(self) -> bool:
        """No direct equivalent for simulating shake on Windows desktop. No-op."""
        app_logger.debug("[Windows] Simulate shake is not applicable for Windows desktop automation. Skipping.")
        return True # Return True as it's not an error, just not implemented

    def type_text(self, text: str) -> bool:
        """Type text using pywinauto send_keys."""
        try:
            send_keys(text) # Types directly to the active window
            app_logger.debug(f"[Windows] Typed text: '{text}'")
            return True
        except Exception as e:
            app_logger.error(f"[Windows] Error typing text: {e}")
            app_logger.debug(f"Full error details: {traceback.format_exc()}")
            return False

    def get_screen_size(self) -> tuple[int, int]:
        """Get the size of the LastWar app window."""
        if not self.main_window:
            app_logger.error("[Windows] Cannot get screen size: LastWar app window not connected.")
            raise RuntimeError("LastWar app window not connected to get size.")
        try:
            rect = self.main_window.rectangle()
            width = rect.width()
            height = rect.height()
            app_logger.debug(f"[Windows] LastWar window size: {width}x{height}")
            return width, height
        except Exception as e:
            app_logger.error(f"[Windows] Failed to get LastWar window size: {e}")
            app_logger.debug(f"Full error details: {traceback.format_exc()}")
            raise RuntimeError(f"Failed to get LastWar window size: {e}")

    def launch_package(self, executable_path: str = CONFIG.get('windows', {}).get('executable_path', '')) -> bool:
        """Launch an application on Windows."""
        try:
            if not executable_path:
                app_logger.error("[Windows] No executable path configured for launching application.")
                return False
            
            Application(backend=self.backend).start(executable_path)
            self.human_delay('launch_wait', 10.0)
            self._connect_to_lastwar_app()
            app_logger.debug(f"[Windows] Launched application: {executable_path}")
            return True
        except Exception as e:
            app_logger.error(f"[Windows] Failed to launch application {executable_path}: {e}")
            app_logger.debug(f"Full error details: {traceback.format_exc()}")
            return False

    def force_stop_package(self, package_name: str = CONFIG.get('windows', {}).get('app_name', '')) -> bool:
        """Force stop an application on Windows."""
        try:
            if not package_name:
                app_logger.error("[Windows] No application name configured for force stopping.")
                return False

            # Try to connect and kill by title (more robust) or process name
            app = Application(backend=self.backend).connect(title_re=f".*{re.escape(package_name)}.*", timeout=1)
            app.kill()
            app_logger.debug(f"[Windows] Force stopped application: {package_name}")
            return True
        except Exception as e:
            app_logger.debug(f"[Windows] Failed to force stop application {package_name}: {e}")
            app_logger.debug(f"Full error details: {traceback.format_exc()}")
            return False

    def get_device_list(self) -> List[str]:
        """For Windows, returns a list containing the logical device ID (e.g., hostname)."""
        app_logger.debug("[Windows] Getting device list (returns current desktop ID).")
        return [self.device_id] # For Windows, the 'device' is typically the local desktop

    def get_connected_device(self) -> Optional[str]:
        """For Windows, returns the logical device ID if pywinauto can connect to desktop."""
        app_logger.debug(f"[Windows] Connected to desktop: {self.device_id}")
        return self.device_id

    def get_current_running_app(self) -> Optional[str]:
        """Returns the title of the currently active window on Windows."""
        try:
            active_window = self.desktop.active_window()
            app_logger.debug(f"[Windows] Current active app: {active_window.window_text()}")
            return active_window.window_text() # Returns the window title
        except Exception as e:
            app_logger.error(f"[Windows] Failed to get current running app: {e}")
            app_logger.debug(f"Full error details: {traceback.format_exc()}")
            return None

    def take_screenshot(self) -> Optional[np.ndarray]:
        """Take screenshot of the LastWar app window and save to tmp/screen.png."""
        if not self.main_window:
            app_logger.error("[Windows] Cannot take screenshot: LastWar app window not connected.")
            return None
        try:
            ensure_dir("tmp")
            output_filepath = 'tmp/screen.png'

            # Capture screenshot of the specific window as a PIL Image
            pil_screenshot = self.main_window.capture_as_image()
            # Convert PIL Image to NumPy array (RGB)
            numpy_screenshot = np.array(pil_screenshot)
            # Convert RGB to BGR (OpenCV's default color order) for correct color representation
            numpy_screenshot = cv2.cvtColor(numpy_screenshot, cv2.COLOR_RGB2BGR)
            
            file_save_executor.submit(self._save_image_to_disk_background, numpy_screenshot, output_filepath)
            return numpy_screenshot
        except Exception as e:
            app_logger.error(f"[Windows] Error taking LastWar app screenshot: {e}")
            app_logger.debug(f"Full error details: {traceback.format_exc()}")
            return None
        
    def cleanup_device_screenshots(self) -> None:
        """No device-side screenshots to clean on Windows. This is a no-op."""
        app_logger.debug("[Windows] No device-side screenshots to clean for Windows.")
        pass # No action needed for Windows desktop

