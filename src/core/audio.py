"""Audio utilities for system sounds and notifications"""

import platform
import sys
from .logging import app_logger

def play_beep(frequency: int = 200, duration: int = 500):
    """Play a system beep sound
    
    Args:
        frequency: Beep frequency in Hz (Windows only)
        duration: Beep duration in milliseconds (Windows only)
    """
    try:
        if platform.system() == "Windows":
            import winsound
            winsound.Beep(frequency, duration)
        else:
            # For Unix systems, print ASCII bell character
            sys.stdout.write('\a')
            sys.stdout.flush()
    except Exception as e:
        app_logger.error(f"Error playing beep: {e}") 