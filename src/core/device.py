"""Device interaction utilities"""

import subprocess
from typing import Optional, Tuple
from .logging import app_logger
from pathlib import Path

def take_screenshot(device_id: str) -> bool:
    """Take a screenshot and save it as screen.png"""
    try:
        result = subprocess.run(
            f"adb -s {device_id} exec-out screencap -p > tmp/screen.png",
            shell=True
        )
        return result.returncode == 0
    except Exception as e:
        app_logger.error(f"Error taking screenshot: {e}")
        return False

def get_screen_size(device_id: str) -> Tuple[int, int]:
    """Get device screen size"""
    try:
        cmd = f"adb -s {device_id} shell wm size"
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            # Parse output like "Physical size: 1080x2400"
            size = result.stdout.strip().split(": ")[1]
            width, height = map(int, size.split("x"))
            return width, height
        else:
            app_logger.error(f"Error getting screen size: {result.stderr}")
            return 540, 960  # Default size
            
    except Exception as e:
        app_logger.error(f"Error getting screen size: {e}")
        return 540, 960  # Default size 

def cleanup_device_screenshots(device_id: str) -> None:
    """Clean up screenshots from device"""
    try:
        cmd = f"adb -s {device_id} shell rm -f /sdcard/screen*.png"
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            app_logger.debug("Cleaned up device screenshots")
        else:
            app_logger.warning(f"Failed to clean device screenshots: {result.stderr}")
    except Exception as e:
        app_logger.error(f"Error cleaning device screenshots: {e}")

def cleanup_temp_files() -> None:
    """Clean up temporary files"""
    try:
        files = Path("tmp").glob("*.png")
        for f in files:
            #f.unlink()
            app_logger.debug(f"Cleaned up temporary file: {f}")
        app_logger.debug("Cleaned up temporary files")
    except Exception as e:
        app_logger.error(f"Error cleaning temporary files: {e}")

def cleanup(device_id: str) -> None:
    """Cleanup device"""
    cleanup_device_screenshots(device_id)
    cleanup_temp_files()

def ensure_dir(path: str) -> None:
    """Ensure directory exists"""
    Path(path).mkdir(exist_ok=True)