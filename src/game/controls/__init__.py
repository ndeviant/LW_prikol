# __init__.py
from src.core.config import CONFIG

# Re-export Controls
from .adb import ADBControls
from .windows import WindowsControls

# Re-export ControlStrategy from strategy.py
from .strategy import ControlStrategy
from .context import Controls

controls = Controls(CONFIG["env"])

# Define __all__ to explicitly list what should be imported
# when someone does 'from src.game.controls import *'
# and, crucially, to hint to Pylance about the intended public API.
__all__ = [
    "ControlStrategy",
    "ADBControls",
    "WindowsControls",
    "Controls",
    "controls"
]