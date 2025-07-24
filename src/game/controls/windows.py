from typing import List, Optional

from src.game.controls.strategy import ControlStrategy

# 2. Concrete Strategies

class WindowsControls(ControlStrategy):
    """
    A Concrete Strategy for controlling a Windows desktop environment.
    (Requires external libraries like pyautogui, win32api for actual implementation)
    """

    def type_text(self, text: str) -> None:
        print(f"[Windows] Typing text: '{text}' on Windows desktop (device: {self.device_id})")
        # import pyautogui
        # pyautogui.write(text)

    def get_screen_size(self) -> tuple[int, int]:
        print(f"[Windows] Getting screen resolution for Windows desktop (device: {self.device_id})")
        # import pyautogui
        # return pyautogui.size()
        return 1920, 1080 # Example resolution for Windows desktop

    def get_device_list(self) -> List[str]:
        print(f"[Windows] Getting list of connected devices (Windows context).")
        # For Windows, this might list monitor IDs or simply return the current machine's ID
        return [self.device_id] # Example

    def launch_package(self, package_name: str) -> None:
        print(f"[Windows] Launching application '{package_name}' on Windows desktop (device: {self.device_id})")
        # import subprocess
        # subprocess.Popen([package_name]) # Or use os.startfile(package_name)

    def force_stop_package(self, package_name: str) -> None:
        print(f"[Windows] Force stopping application '{package_name}' on Windows desktop (device: {self.device_id})")
        # This is complex for Windows, might involve taskkill or finding process by name
        # import os
        # os.system(f"taskkill /IM {package_name}.exe /F") # Example for an .exe

    def press_back(self) -> None:
        print(f"[Windows] Simulating 'back' key press on Windows desktop (device: {self.device_id})")
        # import pyautogui
        # pyautogui.press('browserback') # Or custom key combination

    def tap_screen(self, x: int, y: int) -> None:
        print(f"[Windows] Tapping screen at ({x}, {y}) on Windows desktop (device: {self.device_id})")
        self.click(x, y) # Synonymous with click for Windows

    def swipe_screen(self, start_x: int, start_y: int, end_x: int, end_y: int, duration_ms: int) -> None:
        print(f"[Windows] Swiping screen from ({start_x}, {start_y}) to ({end_x}, {end_y}) for {duration_ms}ms on Windows desktop (device: {self.device_id})")
        self.swipe(start_x, start_y, end_x, end_y, duration_ms) # Synonymous with swipe for Windows

    def get_connected_device(self) -> Optional[str]:
        print(f"[Windows] Getting connected device for {self.device_id}")
        return self.device_id # Example: current machine

    def get_current_running_app(self) -> Optional[str]:
        print(f"[Windows] Getting current running app on Windows desktop (device: {self.device_id})")
        # This is complex for Windows, might involve win32gui or similar to get active window title
        return "Notepad.exe" # Example

    def long_press_screen(self, x: int, y: int, duration_ms: int) -> None:
        print(f"[Windows] Long pressing screen at ({x}, {y}) for {duration_ms}ms on Windows desktop (device: {self.device_id})")
        # import pyautogui
        # pyautogui.mouseDown(x, y)
        # time.sleep(duration_ms / 1000)
        # pyautogui.mouseUp(x, y)

    def simulate_shake(self) -> None:
        print(f"[Windows] Simulating shake gesture on Windows desktop (device: {self.device_id})")
        # No direct equivalent for Windows desktop, might involve custom mouse/keyboard movements.
        # This is a placeholder for demonstration.

