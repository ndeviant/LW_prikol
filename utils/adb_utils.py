# utils/adb_utils.py

import subprocess
import logging

logger = logging.getLogger(__name__)

def get_connected_devices():
    """
    Returns a list of connected device IDs using ADB.
    """
    try:
        result = subprocess.run(
            ['adb', 'devices'],
            capture_output=True,
            text=True,
            check=True
        )
        lines = result.stdout.strip().split('\n')
        devices = [
            line.split('\t')[0] for line in lines[1:] if '\tdevice' in line
        ]
        logger.info(f"Connected devices: {devices}")
        return devices
    except subprocess.CalledProcessError as e:
        logger.exception(f"ADB command failed: {e}")
        return []

def select_device(devices):
    """
    Selects a device from the list of connected devices.
    For simplicity, we select the first device.
    """
    if devices:
        return devices[0]
    else:
        raise Exception("No devices to select from.")

def get_current_running_app(device_id):
    """
    Returns the package name of the currently running app on the device.
    """
    try:
        result = subprocess.run(
            ['adb', '-s', device_id, 'shell', 'dumpsys', 'window', 'windows'],
            capture_output=True,
            text=True,
            check=True
        )
        for line in result.stdout.splitlines():
            if 'mCurrentFocus' in line or 'mFocusedApp' in line:
                package_name = line.split('/')[0].split()[-1]
                logger.debug(f"Current running app: {package_name}")
                return package_name
        return None
    except subprocess.CalledProcessError as e:
        logger.exception(f"Failed to get current running app: {e}")
        return None

def capture_screenshot(device_id, filename='screenshot.png'):
    """
    Captures a screenshot from the device and saves it locally.
    """
    try:
        subprocess.run(
            ['adb', '-s', device_id, 'shell', 'screencap', '-p', f'/sdcard/{filename}'],
            check=True
        )
        subprocess.run(
            ['adb', '-s', device_id, 'pull', f'/sdcard/{filename}', filename],
            check=True
        )
        logger.debug(f"Screenshot saved as {filename}")
        return filename
    except subprocess.CalledProcessError as e:
        logger.exception(f"Failed to capture screenshot: {e}")
        return None

def click_at_location(x, y, device_id):
    """
    Simulates a tap at the specified coordinates on the device screen.
    """
    try:
        subprocess.run(
            ['adb', '-s', device_id, 'shell', 'input', 'tap', str(x), str(y)],
            check=True
        )
        logger.debug(f"Clicked at location ({x}, {y})")
    except subprocess.CalledProcessError as e:
        logger.exception(f"Failed to click at location ({x}, {y}): {e}")

def launch_package(device_id, package_name):
    """
    Launches the specified app package on the device.
    """
    try:
        subprocess.run(
            ['adb', '-s', device_id, 'shell', 'monkey', '-p', package_name, '-c', 'android.intent.category.LAUNCHER', '1'],
            check=True
        )
        logger.info(f"Launched package {package_name}")
    except subprocess.CalledProcessError as e:
        logger.exception(f"Failed to launch package {package_name}: {e}")

def get_screen_size(device_id):
    """
    Returns the screen size (width, height) of the device.
    """
    try:
        result = subprocess.run(
            ['adb', '-s', device_id, 'shell', 'wm', 'size'],
            capture_output=True,
            text=True,
            check=True
        )
        size_str = result.stdout.strip().split(':')[1].strip()
        width, height = map(int, size_str.split('x'))
        logger.debug(f"Screen size: {width}x{height}")
        return width, height
    except subprocess.CalledProcessError as e:
        logger.exception(f"Failed to get screen size: {e}")
        return None, None

def swipe_down(device_id, start_x, start_y, distance, duration=500):
    """
    Swipes down on the device screen from the specified start point by the given distance.
    """
    end_y = start_y + distance
    try:
        subprocess.run(
            ['adb', '-s', device_id, 'shell', 'input', 'swipe',
             str(start_x), str(start_y), str(start_x), str(end_y), str(duration)],
            check=True
        )
        logger.debug(f"Swiped down from ({start_x}, {start_y}) to ({start_x}, {end_y})")
    except subprocess.CalledProcessError as e:
        logger.exception(f"Failed to swipe down: {e}")
