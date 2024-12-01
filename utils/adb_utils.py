# utils/adb_utils.py

import os
import time
import random
import subprocess
from typing import List, Dict, Optional, Tuple
from pathlib import Path

from logging_config import app_logger
from .error_handling import DeviceError
from .device_utils import get_screen_size

def run_adb_command(command: List[str], device_id: Optional[str] = None) -> str:
    """Run an ADB command and return output"""
    try:
        if device_id:
            command = ['adb', '-s', device_id] + command
        else:
            command = ['adb'] + command
            
        result = subprocess.check_output(command).decode('utf-8')
        return result.strip()
        
    except subprocess.CalledProcessError as e:
        app_logger.error(f"ADB command failed: {e}")
        raise DeviceError(f"ADB command failed: {e}")

def humanized_tap(device_id: str, x: int, y: int, variance: int = 5):
    """
    Tap with slight random position variations to seem more human-like.
    Adds random offset of +/- variance pixels to both x and y coordinates.
    """
    try:
        width, height = get_screen_size(device_id)
        
        # Add slight random variations to coordinates
        actual_x = x + random.randint(-variance, variance)
        actual_y = y + random.randint(-variance, variance)
        
        # Ensure coordinates stay within reasonable bounds
        actual_x = max(0, min(actual_x, width))
        actual_y = max(0, min(actual_y, height))
        
        run_adb_command([
            'shell', 'input', 'tap',
            str(actual_x), str(actual_y)
        ], device_id)
        
        # Add slight random delay after tap
        time.sleep(random.uniform(0.1, 0.3))
        
    except Exception as e:
        app_logger.error(f"Error with humanized tap at ({x}, {y}): {e}")
        raise DeviceError(f"Error with humanized tap: {e}")

def humanized_swipe(device_id: str, start_x: int, start_y: int, end_x: int, end_y: int, base_duration: int = 300):
    """
    Perform swipe with human-like variations in speed and position
    """
    try:
        width, height = get_screen_size(device_id)
        
        # Add slight random variations to coordinates
        actual_start_x = start_x + random.randint(-10, 10)
        actual_start_y = start_y + random.randint(-10, 10)
        actual_end_x = end_x + random.randint(-10, 10)
        actual_end_y = end_y + random.randint(-10, 10)
        
        # Ensure coordinates stay within screen bounds
        actual_start_x = max(0, min(actual_start_x, width))
        actual_start_y = max(0, min(actual_start_y, height))
        actual_end_x = max(0, min(actual_end_x, width))
        actual_end_y = max(0, min(actual_end_y, height))
        
        # Vary the swipe duration
        duration = base_duration + random.randint(-50, 50)
        
        run_adb_command([
            'shell', 'input', 'swipe',
            str(actual_start_x), str(actual_start_y),
            str(actual_end_x), str(actual_end_y),
            str(duration)
        ], device_id)
        
        # Add slight random delay after swipe
        time.sleep(random.uniform(0.2, 0.4))
        
    except Exception as e:
        app_logger.error(f"Error performing humanized swipe: {e}")
        raise DeviceError(f"Error performing humanized swipe: {e}")

def swipe_up(device_id: str, distance: int = 300):
    """Swipe up on screen with human-like variations"""
    try:
        width, height = get_screen_size(device_id)
        
        # Add slight horizontal variation to seem more human
        center_x = (width // 2) + random.randint(-30, 30)
        start_y = (height * 2) // 3
        end_y = start_y - distance
        
        humanized_swipe(device_id, center_x, start_y, center_x, end_y)
        
    except Exception as e:
        app_logger.error(f"Error performing swipe up: {e}")
        raise DeviceError(f"Error performing swipe up: {e}")

def press_back(device_id: str):
    """Press the back button"""
    try:
        run_adb_command(['shell', 'input', 'keyevent', 'KEYCODE_BACK'], device_id)
    except Exception as e:
        app_logger.error(f"Failed to press back button: {e}")
        raise

def launch_package(device_id: str, package_name: str):
    """Launch an app package"""
    try:
        run_adb_command(['shell', 'monkey', '-p', package_name, '-c', 'android.intent.category.LAUNCHER', '1'], device_id)
    except Exception as e:
        app_logger.error(f"Failed to launch package {package_name}: {e}")
        raise

def force_stop_package(device_id: str, package_name: str):
    """Force stop an app package"""
    try:
        run_adb_command(['shell', 'am', 'force-stop', package_name], device_id)
    except Exception as e:
        app_logger.error(f"Failed to force stop package {package_name}: {e}")
        raise

def get_device_list() -> List[str]:
    """Get list of connected devices"""
    try:
        result = subprocess.run(['adb', 'devices'], capture_output=True, text=True)
        if result.returncode != 0:
            app_logger.error(f"Failed to get device list: {result.stderr}")
            return []
            
        # Parse output to get device IDs
        devices = []
        for line in result.stdout.splitlines()[1:]:  # Skip first line (header)
            if line.strip():
                device_id = line.split()[0]
                devices.append(device_id)
                
        return devices
        
    except Exception as e:
        app_logger.error(f"Error getting device list: {e}")
        return []
