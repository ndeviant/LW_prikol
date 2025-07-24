"""Game automation package"""

# Import the 'controls' instance from the 'controls' subpackage
# This assumes src/game/controls/__init__.py correctly defines 'controls'
from .controls import controls

# Optionally, define __all__ to explicitly declare what's part of the public API
# when someone does 'from src.game import *'
__all__ = ["controls"] # Only expose the 'controls' instance for 'from game import *'