# __init__.py

from .controls import GameControls, controls

# Define __all__ to explicitly list what should be imported
# when someone does 'from src.game import *'
# and, crucially, to hint to Pylance about the intended public API.
__all__ = [
    "GameControls",
    "controls"
]