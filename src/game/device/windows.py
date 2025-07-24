import subprocess
from typing import Any, List, Optional, Union
import time
import os
import re
import traceback
import pywinauto
from pywinauto import Desktop, Application, findwindows 
from pywinauto.keyboard import send_keys
import pyautogui # For simpler mouse/keyboard actions not directly covered by pywinauto's element methods
from PIL import Image # pyautogui uses PIL for screenshots

from src.core.config import CONFIG
from src.core.helpers import ensure_dir
from src.core.logging import app_logger

from .strategy import ControlStrategy

# 2. Concrete Strategies

class WindowsControls(ControlStrategy):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.device_id = os.getlogin()
        self.app_name = CONFIG['windows']['app_name']
        self.executable_path = CONFIG['windows']['executable_path']

        self.app = None # pywinauto.Application instance
        self.main_window = None # pywinauto.WindowSpecification or Wrapper object for the main app window
        self.desktop = Desktop(backend="win32") # Use 'uia' for modern apps, 'win32' for older ones

        # Attempt to connect to the LastWar application immediately
        self._connect_to_lastwar_app()
        app_logger.info(f"[Windows] Initialized WindowsControls for '{self.device_id}'. App connection status: {'Connected' if self.app and self.main_window else 'Failed'}")

    def _connect_to_lastwar_app(self) -> bool:
        """Helper to connect to the LastWar application and get its main window."""

        if not (self.app_name or self.executable_path):
            app_logger.error("[Windows] No application identifier (name, path, or process name) configured for LastWar.")
            return False

        try:
            # Prioritize connecting by process name or path for robustness
            if self.executable_path:
                app_logger.debug(f"[Windows] Attempting to connect to LastWar by path: {self.executable_path}")
                self.app = Application(backend="uia").connect(path=self.executable_path, timeout=10)
            elif self.app_name:
                app_logger.debug(f"[Windows] Attempting to connect to LastWar by title_re: .*{re.escape(self.app_name)}.*")
                self.app = Application(backend="uia").connect(title_re=f".*{re.escape(self.app_name)}.*", timeout=10)
            else:
                app_logger.error("[Windows] No valid connection criteria for LastWar app.")
                return False

            # Get the main window of the connected application
            # Use wait_until_passes to ensure the window is ready
            self.main_window = self.app.top_window() # This gets the WindowSpecification
            self.main_window.wait('ready', timeout=5) # Wait for the window to be ready (visible, enabled)
            
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
        """Check if the target application is running on Windows."""
        try:
            # Try to connect to the application by title or process name
            # Assuming CONFIG['app_name'] or CONFIG['app_executable'] holds the target app info
            app_name = CONFIG.get('windows', {}).get('app_name')
            if not app_name:
                app_logger.warning("[Windows] No application name configured for 'is_app_running'.")
                return False
            
            # This is a heuristic, connecting might raise if not found
            app = Application(backend="uia").connect(title_re=f".*{re.escape(app_name)}.*", timeout=1)
            # Or by process name: app = Application(backend="uia").connect(path=app_executable_path, timeout=1)
            app_logger.debug(f"[Windows] App '{app_name}' is running.")
            return True
        
        except Exception:
            app_logger.debug(f"[Windows] App '{app_name}' is not running.")
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
            pyautogui.dragTo(end_x, end_y, duration=duration_ms / 1000.0) # pyautogui duration is in seconds
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
        app_logger.info("[Windows] Simulate shake is not applicable for Windows desktop automation. Skipping.")
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
        """Get Windows screen resolution using pyautogui."""
        try:
            width, height = pyautogui.size()
            app_logger.debug(f"[Windows] Screen size: {width}x{height}")
            return width, height
        except Exception as e:
            app_logger.error(f"[Windows] Failed to get screen size: {e}")
            app_logger.debug(f"Full error details: {traceback.format_exc()}")
            raise RuntimeError(f"Failed to get screen size: {e}")

    def launch_package(self, package_name: str = CONFIG.get('windows', {}).get('executable_path', '')) -> bool:
        """Launch an application on Windows."""
        try:
            if not package_name:
                app_logger.error("[Windows] No executable path configured for launching application.")
                return False
            Application(backend="uia").start(package_name)
            app_logger.info(f"[Windows] Launched application: {package_name}")
            return True
        except Exception as e:
            app_logger.error(f"[Windows] Failed to launch application {package_name}: {e}")
            app_logger.debug(f"Full error details: {traceback.format_exc()}")
            return False

    def force_stop_package(self, package_name: str = CONFIG.get('windows', {}).get('app_name', '')) -> bool:
        """Force stop an application on Windows."""
        try:
            if not package_name:
                app_logger.error("[Windows] No application name configured for force stopping.")
                return False
            
            # Try to connect and kill by title (more robust) or process name
            app = Application(backend="uia").connect(title_re=f".*{re.escape(package_name)}.*", timeout=5)
            app.kill()
            app_logger.info(f"[Windows] Force stopped application: {package_name}")
            return True
        except Exception as e:
            app_logger.error(f"[Windows] Failed to force stop application {package_name}: {e}")
            app_logger.debug(f"Full error details: {traceback.format_exc()}")
            return False

    def get_device_list(self) -> List[str]:
        """For Windows, returns a list containing the logical device ID (e.g., hostname)."""
        app_logger.debug("[Windows] Getting device list (returns current desktop ID).")
        return [self.device_id] # For Windows, the 'device' is typically the local desktop

    def get_connected_device(self) -> Optional[str]:
        """For Windows, returns the logical device ID if pywinauto can connect to desktop."""
        try:
            # _ = self.desktop.top_window() # Try to get any window to confirm desktop is accessible

            app_logger.debug(f"[Windows] Connected to desktop: {self.device_id}")
            return self.device_id
        except Exception as e:
            app_logger.error(f"[Windows] Failed to connect to desktop: {e}")
            app_logger.debug(f"Full error details: {traceback.format_exc()}")
            return None

    def get_current_running_app(self) -> Optional[str]:
        """Returns the title of the currently active window on Windows."""
        try:
            active_window = self.desktop.top_window()
            app_logger.debug(f"[Windows] Current active app: {active_window.window_text()}")
            return active_window.window_text() # Returns the window title
        except Exception as e:
            app_logger.error(f"[Windows] Failed to get current running app: {e}")
            app_logger.debug(f"Full error details: {traceback.format_exc()}")
            return None

    def take_screenshot(self) -> bool:
        """Take screenshot of the entire screen using pyautogui and save to tmp/screen.png."""
        try:
            ensure_dir("tmp")
            screenshot = pyautogui.screenshot()
            screenshot.save('tmp/screen.png')
            return True
        except Exception as e:
            app_logger.error(f"[Windows] Error taking screenshot: {e}")
            app_logger.debug(f"Full error details: {traceback.format_exc()}")
            return False
        
    def cleanup_device_screenshots(self) -> None:
        """No device-side screenshots to clean on Windows. This is a no-op."""
        app_logger.debug("[Windows] No device-side screenshots to clean for Windows.")
        pass # No action needed for Windows desktop

