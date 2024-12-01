import os
import time
import subprocess
from typing import List, Optional, Tuple
from logging_config import app_logger
from pathlib import Path

def capture_screenshot(device_id: str, filename: Optional[str] = None) -> Optional[str]:
    """Capture screenshot from device"""
    try:
        # Ensure tmp directory exists
        tmp_dir = Path('tmp')
        tmp_dir.mkdir(exist_ok=True)
        
        # Use tmp directory for local file
        timestamp = int(time.time())
        filename = filename or str(tmp_dir / f'screenshot_{timestamp}.png')
        remote_path = f'/sdcard/tmp/screenshot_{timestamp}.png'
        
        # Ensure remote tmp directory exists
        subprocess.run([
            'adb', '-s', device_id, 'shell',
            'mkdir', '-p', '/sdcard/tmp'
        ], check=True)
        
        # Capture screenshot on device
        subprocess.run([
            'adb', '-s', device_id, 'shell',
            'screencap', '-p', remote_path
        ], check=True)
        
        # Pull screenshot to local machine
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        subprocess.run([
            'adb', '-s', device_id, 'pull',
            remote_path, filename
        ], check=True)
        
        # Clean up remote file and directory
        subprocess.run([
            'adb', '-s', device_id, 'shell',
            'rm', '-f', remote_path
        ], check=True)
        
        # Clean up remote tmp directory if empty
        subprocess.run([
            'adb', '-s', device_id, 'shell',
            'rmdir', '/sdcard/tmp'
        ], check=False)  # Don't fail if directory not empty
        
        return filename if os.path.exists(filename) else None
        
    except Exception as e:
        app_logger.error(f"Error capturing screenshot: {e}")
        return None

def find_all_matches(
    screenshot_path: str,
    template_path: str,
    threshold: float = 0.8
) -> List[Tuple[int, int]]:
    """Find all matches of template in screenshot above threshold"""
    try:
        import cv2
        import numpy as np
        
        # Read images
        screenshot = cv2.imread(screenshot_path)
        template = cv2.imread(template_path)
        
        if screenshot is None or template is None:
            app_logger.error("Failed to read images")
            return []
            
        # Match template
        result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
        locations = np.where(result >= threshold)
        
        # Get match coordinates
        matches = []
        for pt in zip(*locations[::-1]):
            x = pt[0] + template.shape[1] // 2
            y = pt[1] + template.shape[0] // 2
            matches.append((x, y))
            
        return matches
        
    except Exception as e:
        app_logger.error(f"Error finding matches: {e}")
        return []

def find_on_screen(
    screenshot_path: str,
    template_path: str,
    threshold: float = 0.8
) -> Optional[Tuple[int, int]]:
    """Find first match of template in screenshot above threshold"""
    matches = find_all_matches(screenshot_path, template_path, threshold)
    return matches[0] if matches else None 