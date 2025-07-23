from abc import ABC, abstractmethod
from typing import Dict, Any, List, Literal, Optional

# 1. Strategy Interface
class ControlStrategy(ABC):
    """
    The Strategy Interface declares operations common to all supported versions
    of some algorithm. The Context uses this interface to call the algorithm
    defined by Concrete Strategies.
    """
    def __init__(self, device_id: str):
        self.device_id = device_id

    @abstractmethod
    def click(self, x: int, y: int) -> None:
        """Simulates a click at given coordinates."""
        pass

    @abstractmethod
    def swipe(self, start_x: int, start_y: int, end_x: int, end_y: int, duration_ms: int) -> None:
        """Simulates a swipe gesture."""
        pass

    @abstractmethod
    def type_text(self, text: str) -> None:
        """Types a given string of text."""
        pass

    @abstractmethod
    def get_screen_resolution(self) -> tuple[int, int]:
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
    def tap_screen(self, x: int, y: int) -> None:
        """Simulates a tap on the screen at given coordinates."""
        # This is often synonymous with 'click', but kept separate if distinct behavior is needed.
        pass

    @abstractmethod
    def swipe_screen(self, start_x: int, start_y: int, end_x: int, end_y: int, duration_ms: int) -> None:
        """Simulates a swipe gesture on the screen."""
        # Synonymous with 'swipe', but kept for clarity if preferred.
        pass

    @abstractmethod
    def get_connected_device(self) -> Optional[str]:
        """Returns the ID of the currently connected device, or None if none."""
        pass

    @abstractmethod
    def get_current_running_app(self) -> Optional[str]:
        """Returns the package name of the currently running foreground application."""
        pass

    @abstractmethod
    def long_press_screen(self, x: int, y: int, duration_ms: int) -> None:
        """Simulates a long press on the screen at given coordinates."""
        pass

    @abstractmethod
    def get_screen_size(self) -> tuple[int, int]:
        """Returns the screen size (width, height). Synonymous with get_screen_resolution."""
        pass

    @abstractmethod
    def simulate_shake(self) -> None:
        """Simulates a shake gesture on the device."""
        pass


# 2. Concrete Strategies
class ADBControls(ControlStrategy):
    """
    A Concrete Strategy for controlling a device via ADB commands.
    """
    def click(self, x: int, y: int) -> None:
        print(f"[ADB] Clicking at ({x}, {y}) on device {self.device_id}")
        # import subprocess
        # subprocess.run(['adb', '-s', self.device_id, 'shell', 'input', 'tap', str(x), str(y)])

    def swipe(self, start_x: int, start_y: int, end_x: int, end_y: int, duration_ms: int) -> None:
        print(f"[ADB] Swiping from ({start_x}, {start_y}) to ({end_x}, {end_y}) for {duration_ms}ms on device {self.device_id}")
        # subprocess.run(['adb', '-s', self.device_id, 'shell', 'input', 'swipe', str(start_x), str(start_y), str(end_x), str(end_y), str(duration_ms)])

    def type_text(self, text: str) -> None:
        print(f"[ADB] Typing text: '{text}' on device {self.device_id}")
        # subprocess.run(['adb', '-s', self.device_id, 'shell', 'input', 'text', text])

    def get_screen_resolution(self) -> tuple[int, int]:
        print(f"[ADB] Getting screen resolution for device {self.device_id}")
        # In a real scenario, parse 'wm size' output
        return 1080, 1920 # Example resolution for ADB device

    def get_device_list(self) -> List[str]:
        print(f"[ADB] Getting list of connected devices.")
        # import subprocess
        # result = subprocess.run(['adb', 'devices'], capture_output=True, text=True)
        # Parse result.stdout to get device IDs
        return [self.device_id, "another_adb_device"] # Example

    def launch_package(self, package_name: str) -> None:
        print(f"[ADB] Launching package '{package_name}' on device {self.device_id}")
        # import subprocess
        # subprocess.run(['adb', '-s', self.device_id, 'shell', 'monkey', '-p', package_name, '-c', 'android.intent.category.LAUNCHER', '1'])

    def force_stop_package(self, package_name: str) -> None:
        print(f"[ADB] Force stopping package '{package_name}' on device {self.device_id}")
        # import subprocess
        # subprocess.run(['adb', '-s', self.device_id, 'shell', 'am', 'force-stop', package_name])

    def press_back(self) -> None:
        print(f"[ADB] Pressing back button on device {self.device_id}")
        # import subprocess
        # subprocess.run(['adb', '-s', self.device_id, 'shell', 'input', 'keyevent', '4']) # KEYCODE_BACK

    def tap_screen(self, x: int, y: int) -> None:
        print(f"[ADB] Tapping screen at ({x}, {y}) on device {self.device_id}")
        # Synonymous with click for ADB, but could have distinct implementation
        self.click(x, y)

    def swipe_screen(self, start_x: int, start_y: int, end_x: int, end_y: int, duration_ms: int) -> None:
        print(f"[ADB] Swiping screen from ({start_x}, {start_y}) to ({end_x}, {end_y}) for {duration_ms}ms on device {self.device_id}")
        # Synonymous with swipe for ADB, but could have distinct implementation
        self.swipe(start_x, start_y, end_x, end_y, duration_ms)

    def get_connected_device(self) -> Optional[str]:
        print(f"[ADB] Getting connected device for {self.device_id}")
        # In a real scenario, check if self.device_id is actually connected
        return self.device_id # Example

    def get_current_running_app(self) -> Optional[str]:
        print(f"[ADB] Getting current running app on device {self.device_id}")
        # import subprocess
        # result = subprocess.run(['adb', '-s', self.device_id, 'shell', 'dumpsys', 'activity', 'activities'], capture_output=True, text=True)
        # Parse result.stdout for current app
        return "com.example.currentapp" # Example

    def long_press_screen(self, x: int, y: int, duration_ms: int) -> None:
        print(f"[ADB] Long pressing screen at ({x}, {y}) for {duration_ms}ms on device {self.device_id}")
        # import subprocess
        # subprocess.run(['adb', '-s', self.device_id, 'shell', 'input', 'swipe', str(x), str(y), str(x), str(y), str(duration_ms)])

    def get_screen_size(self) -> tuple[int, int]:
        print(f"[ADB] Getting screen size for device {self.device_id}")
        return self.get_screen_resolution() # Same as get_screen_resolution

    def simulate_shake(self) -> None:
        print(f"[ADB] Simulating shake gesture on device {self.device_id}")
        # ADB does not have a direct 'shake' command, might involve complex sequence or specific emulator features.
        # This is a placeholder for demonstration.


class WindowsControls(ControlStrategy):
    """
    A Concrete Strategy for controlling a Windows desktop environment.
    (Requires external libraries like pyautogui, win32api for actual implementation)
    """
    def click(self, x: int, y: int) -> None:
        print(f"[Windows] Clicking at ({x}, {y}) on Windows desktop (device: {self.device_id})")
        # import pyautogui
        # pyautogui.click(x, y)

    def swipe(self, start_x: int, start_y: int, end_x: int, end_y: int, duration_ms: int) -> None:
        print(f"[Windows] Swiping from ({start_x}, {start_y}) to ({end_x}, {end_y}) for {duration_ms}ms on Windows desktop (device: {self.device_id})")
        # import pyautogui
        # pyautogui.moveTo(start_x, start_y)
        # pyautogui.dragTo(end_x, end_y, duration=duration_ms / 1000)

    def type_text(self, text: str) -> None:
        print(f"[Windows] Typing text: '{text}' on Windows desktop (device: {self.device_id})")
        # import pyautogui
        # pyautogui.write(text)

    def get_screen_resolution(self) -> tuple[int, int]:
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

    def get_screen_size(self) -> tuple[int, int]:
        print(f"[Windows] Getting screen size for Windows desktop (device: {self.device_id})")
        return self.get_screen_resolution() # Same as get_screen_resolution

    def simulate_shake(self) -> None:
        print(f"[Windows] Simulating shake gesture on Windows desktop (device: {self.device_id})")
        # No direct equivalent for Windows desktop, might involve custom mouse/keyboard movements.
        # This is a placeholder for demonstration.


# 3. Context
class Controls:
    """
    The Context maintains a reference to one of the Concrete Strategy objects.
    The Context does not know the concrete class of a strategy. It should
    work with all strategies via the Strategy interface.
    """
    def __init__(self, device_id: str, control_type: Literal["adb", "windows"]) -> None:
        self._device_id = device_id
        self._control_strategy: ControlStrategy

        # The "setting" determines which strategy to use
        if control_type.lower() == "adb":
            self._control_strategy = ADBControls(device_id)
        elif control_type.lower() == "windows":
            self._control_strategy = WindowsControls(device_id)
        else:
            raise ValueError(f"Unknown control type: {control_type}. Choose 'adb' or 'windows'.")

        print(f"Controls initialized for device '{self._device_id}' with {type(self._control_strategy).__name__} strategy.")

    # The Context delegates some part of its behavior to the chosen Strategy object.
    def click(self, x: int, y: int) -> None:
        self._control_strategy.click(x, y)

    def swipe(self, start_x: int, start_y: int, end_x: int, end_y: int, duration_ms: int) -> None:
        self._control_strategy.swipe(start_x, start_y, end_x, end_y, duration_ms)

    def type_text(self, text: str) -> None:
        self._control_strategy.type_text(text)

    def get_screen_resolution(self) -> tuple[int, int]:
        return self._control_strategy.get_screen_resolution()

    def get_device_list(self) -> List[str]:
        return self._control_strategy.get_device_list()

    def launch_package(self, package_name: str) -> None:
        self._control_strategy.launch_package(package_name)

    def force_stop_package(self, package_name: str) -> None:
        self._control_strategy.force_stop_package(package_name)

    def press_back(self) -> None:
        self._control_strategy.press_back()

    def tap_screen(self, x: int, y: int) -> None:
        self._control_strategy.tap_screen(x, y)

    def swipe_screen(self, start_x: int, start_y: int, end_x: int, end_y: int, duration_ms: int) -> None:
        self._control_strategy.swipe_screen(start_x, start_y, end_x, end_y, duration_ms)

    def get_connected_device(self) -> Optional[str]:
        return self._control_strategy.get_connected_device()

    def get_current_running_app(self) -> Optional[str]:
        return self._control_strategy.get_current_running_app()

    def long_press_screen(self, x: int, y: int, duration_ms: int) -> None:
        self._control_strategy.long_press_screen(x, y, duration_ms)

    def get_screen_size(self) -> tuple[int, int]:
        return self._control_strategy.get_screen_size()

    def simulate_shake(self) -> None:
        self._control_strategy.simulate_shake()


# --- Client Code ---
# The client uses the 'Controls' class, unaware of the specific underlying implementation.

print("--- Scenario 1: Using ADB Controls ---")
adb_device_id = "emulator-5554"
adb_controls = Controls(device_id=adb_device_id, control_type="adb")
adb_controls.click(100, 200)
adb_controls.type_text("hello adb world")
adb_controls.swipe(500, 1000, 500, 200, 500)
width, height = adb_controls.get_screen_resolution()
print(f"ADB device resolution: {width}x{height}")

# New method calls for ADB
print("\n--- New ADB Control Methods ---")
print(f"Connected ADB devices: {adb_controls.get_device_list()}")
adb_controls.launch_package("com.example.game")
adb_controls.tap_screen(10, 10)
adb_controls.long_press_screen(300, 300, 1500)
adb_controls.press_back()
print(f"Current ADB app: {adb_controls.get_current_running_app()}")
adb_controls.force_stop_package("com.example.game")
adb_controls.simulate_shake()


print("\n--- Scenario 2: Using Windows Controls ---")
windows_device_id = "my-desktop-pc" # A logical ID for the Windows machine
windows_controls = Controls(device_id=windows_device_id, control_type="windows")
windows_controls.click(50, 50)
windows_controls.type_text("hello windows world")
windows_controls.swipe(900, 500, 100, 500, 300)
width, height = windows_controls.get_screen_resolution()
print(f"Windows desktop resolution: {width}x{height}")

# New method calls for Windows
print("\n--- New Windows Control Methods ---")
print(f"Connected Windows devices: {windows_controls.get_device_list()}")
windows_controls.launch_package("notepad.exe")
windows_controls.tap_screen(20, 20)
windows_controls.long_press_screen(400, 400, 2000)
windows_controls.press_back()
print(f"Current Windows app: {windows_controls.get_current_running_app()}")
windows_controls.force_stop_package("notepad.exe")
windows_controls.simulate_shake()


print("\n--- Scenario 3: Invalid Control Type ---")
try:
    invalid_controls = Controls(device_id="unknown", control_type="linux")
except ValueError as e:
    print(f"Error: {e}")