# __init__.py
from src.core.config import CONFIG

# Re-export Device
from .adb import ADBDevice
from .windows import WindowsDevice

# Re-export DeviceStrategy from strategy.py
from .strategy import DeviceStrategy
from .device import DeviceContext, device

# Define __all__ to explicitly list what should be imported
# when someone does 'from src.game.device import *'
# and, crucially, to hint to Pylance about the intended public API.
__all__ = [
    "DeviceStrategy",
    "ADBDevice",
    "WindowsDevice",
    "DeviceContext",
    "device"
]