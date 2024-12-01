import subprocess
from typing import Tuple
from logging_config import app_logger

def get_screen_size(device_id: str) -> Tuple[int, int]:
    """Get device screen size"""
    try:
        output = subprocess.check_output([
            'adb', '-s', device_id, 'shell', 'wm', 'size'
        ]).decode('utf-8')
        width, height = map(int, output.split()[-1].split('x'))
        return width, height
    except Exception as e:
        app_logger.error(f"Error getting screen size: {e}")
        raise 