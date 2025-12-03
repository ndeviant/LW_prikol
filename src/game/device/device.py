from typing import List, Optional, Literal

import numpy as np

from .strategy import DeviceStrategy
from .adb import ADBDevice
from .windows import WindowsDevice
from src.core.logging import app_logger
from src.core.config import CONFIG

swipe_cfg = CONFIG['ui_elements']['swipe']

# 3. Context
class DeviceContext:
    _instance: Optional['DeviceContext'] = None
    _initialized: bool = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    """
    The Context maintains a reference to one of the Concrete Strategy objects.
    The Context does not know the concrete class of a strategy. It should
    work with all strategies via the Strategy interface.
    """
    def __init__(self, device_type: Literal["adb", "windows"] = "adb") -> None:
        if self._initialized:
            return
        
        self._device_strategy: DeviceStrategy

        # The "setting" determines which strategy to use
        if device_type.lower() == "adb":
            self._device_strategy = ADBDevice()
        elif device_type.lower() == "windows":
            self._device_strategy = WindowsDevice()
        else:
            raise ValueError(f"Unknown device type: {device_type}. Choose 'adb' or 'windows'.")

        app_logger.debug(f"Device initialized for '{device_type}' device with {type(self._device_strategy).__name__} strategy.")

    # The Context delegates some part of its behavior to the chosen Strategy object.
    @property
    def is_app_running(self) -> bool:
        return self._device_strategy.is_app_running
    
    def click(self, x: int, y: int, duration: float = 0, delay='tap_delay', critical=False) -> None:
        return self._device_strategy.click(x, y, duration, delay, critical)

    def swipe(
            self, 
            direction: str = "up", 
            num_swipes: int = 1, 
            duration_ms: int = CONFIG['timings']['swipe_duration']['min'],
            start = (
                swipe_cfg['start_x'], 
                swipe_cfg['start_y']
            ), 
            end = (
                swipe_cfg['end_x'], 
                swipe_cfg['end_y']
            )
        ) -> None:
        return self._device_strategy.swipe(direction, num_swipes, duration_ms, start=start, end=end)

    def type_text(self, text: str) -> None:
        return self._device_strategy.type_text(text)

    def launch_package(self, *args, **kwargs) -> bool:
        return self._device_strategy.launch_package(*args, **kwargs)

    def force_stop_package(self, *args, **kwargs) -> None:
        return self._device_strategy.force_stop_package(*args, **kwargs)

    def get_screen_size(self) -> tuple[int, int]:
        return self._device_strategy.get_screen_size()

    def get_device_list(self) -> List[str]:
        return self._device_strategy.get_device_list()

    def press_back(self) -> None:
        return self._device_strategy.press_back()

    def get_connected_device(self) -> Optional[str]:
        return self._device_strategy.get_connected_device()

    def simulate_shake(self) -> None:
        return self._device_strategy.simulate_shake()

    def take_screenshot(self) -> Optional[np.ndarray]:
        return self._device_strategy.take_screenshot()

    def cleanup_device_screenshots(self) -> None:
        return self._device_strategy.cleanup_device_screenshots()

    def human_delay(self, *args, **kwargs) -> None:
        return self._device_strategy.human_delay(*args, **kwargs)
    
    def spam_click(self, x, y, duration=3, delay=0):
        return self._device_strategy.spam_click(x, y, duration=duration, critical=False, delay=delay)
    
    def cleanup_temp_files(self) -> None:
        return self._device_strategy.cleanup_temp_files()
    
device: DeviceContext = DeviceContext(CONFIG["env"])