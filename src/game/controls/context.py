from typing import List, Literal, Optional

from src.core.config import CONFIG
from src.core.logging import app_logger
from src.game.controls.strategy import ControlStrategy
from src.game.controls.adb import ADBControls
from src.game.controls.windows import WindowsControls

# 3. Context
class Controls:
    """
    The Context maintains a reference to one of the Concrete Strategy objects.
    The Context does not know the concrete class of a strategy. It should
    work with all strategies via the Strategy interface.
    """
    def __init__(self, control_type: Literal["adb", "windows"] = "adb") -> None:
        self._control_strategy: ControlStrategy

        # The "setting" determines which strategy to use
        if control_type.lower() == "adb":
            self._control_strategy = ADBControls()
        elif control_type.lower() == "windows":
            self._control_strategy = WindowsControls()
        else:
            raise ValueError(f"Unknown control type: {control_type}. Choose 'adb' or 'windows'.")

        app_logger.debug(f"Controls initialized for '{control_type}' device with {type(self._control_strategy).__name__} strategy.")

    # The Context delegates some part of its behavior to the chosen Strategy object.
    @property
    def is_app_running(self) -> bool:
        return self._control_strategy.is_app_running
    
    def click(self, x: int, y: int, duration: float = CONFIG['timings']['tap_delay']) -> None:
        return self._control_strategy.click(x, y, duration)

    def swipe(self, direction: str, num_swipes: int, duration_ms: int = CONFIG['timings']['swipe_duration']['min']) -> None:
        return self._control_strategy.swipe(direction, num_swipes, duration_ms)

    def type_text(self, text: str) -> None:
        return self._control_strategy.type_text(text)

    def launch_game(self) -> None:
        return self._control_strategy.launch_game()

    def launch_package(self, package_name: str) -> None:
        return self._control_strategy.launch_package(package_name)

    def force_stop_package(self, package_name: str) -> None:
        return self._control_strategy.force_stop_package(package_name)

    def navigate_home(self, force: bool) -> None:
        return self._control_strategy.navigate_home(force)

    def check_active_on_another_device(self) -> None:
        return self._control_strategy.check_active_on_another_device()

    def get_screen_size(self) -> tuple[int, int]:
        return self._control_strategy.get_screen_size()

    def get_device_list(self) -> List[str]:
        return self._control_strategy.get_device_list()

    def press_back(self) -> None:
        return self._control_strategy.press_back()

    def get_connected_device(self) -> Optional[str]:
        return self._control_strategy.get_connected_device()

    def get_current_running_app(self) -> Optional[str]:
        return self._control_strategy.get_current_running_app()

    def simulate_shake(self) -> None:
        return self._control_strategy.simulate_shake()

    def human_delay(self, delay) -> None:
        return self._control_strategy.human_delay(delay)

