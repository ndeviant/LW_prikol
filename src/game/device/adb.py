import os
import random
import re
import subprocess
import time
import traceback
from pathlib import Path
from typing import List, Optional
import numpy as np
from typing import Optional
import concurrent.futures
import cv2

from src.core.config import CONFIG
from src.core.helpers import ensure_dir
from src.core.logging import app_logger
from .strategy import ControlStrategy

file_save_executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)

# 2. Concrete Strategies
class ADBControls(ControlStrategy):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.device_id = None
        self.device_id = self.get_connected_device()

    @property
    def is_app_running(self) -> bool:
        # Check if game is running first
        current_app = self.get_current_running_app()
        if current_app == CONFIG['adb']['package_name']:
            return True

    """
    A Concrete Strategy for controlling a device via ADB commands.
    """
    def _perform_click(self, x: int, y: int, duration_ms: int) -> bool:
        """Execute a long press at coordinates with specified duration
        
        Args:
            device_id: Device identifier
            x: X coordinate
            y: Y coordinate
            duration: Press duration in milliseconds
        """

        if not duration_ms:
            duration_ms = int(100 * random.uniform(0.8, 1.2))
        
        device_id: str = self.device_id

        try:
            cmd = f"{CONFIG.adb['binary_path']} -s {device_id} shell input swipe {x} {y} {x} {y} {duration_ms}"
            subprocess.run(cmd, shell=True, check=True)
            return True
        
        except subprocess.CalledProcessError:
            app_logger.error(f"Failed to execute long press on device {device_id}")
            return False

    def _perform_swipe(self, start_x: int, start_y: int, end_x: int, end_y: int, duration_ms: int = 300) -> bool:
        """Swipe screen from start to end coordinates"""
        try:
            cmd = f"{CONFIG.adb['binary_path']} -s {self.device_id} shell input swipe {start_x} {start_y} {end_x} {end_y} {duration_ms}"
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
            
        except Exception as e:
            app_logger.error(f"Error swiping screen: {e}")
            return False

    def press_back(self) -> bool:
        """Press back button"""
        try:
            cmd = f"{CONFIG.adb['binary_path']} -s {self.device_id} shell input keyevent 4"
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
            
        except Exception as e:
            app_logger.error(f"Error pressing back: {e}")
            return False
        
    def simulate_shake(device_id: str, duration_ms: int = 1000) -> bool:
        """Simulate device shake using appropriate method for emulator or real device
        
        Args:
            device_id: The device identifier
            duration_ms: Duration of shake in milliseconds (default 1000ms)
        
        Returns:
            bool: True if shake simulation succeeded, False otherwise
        """
        try:
            # Check if device is an emulator
            app_logger.debug("Using emulator shake simulation")
            
            # Different shake patterns
            shake_patterns = [
                # Strong side shake
                ("100:0:9.81", "-100:0:9.81"),
                # Strong up/down shake
                ("0:100:9.81", "0:-100:9.81"),
                # Diagonal shake
                ("100:100:9.81", "-100:-100:9.81"),
                # Very strong shake
                ("200:200:9.81", "-200:-200:9.81"),
            ]
            
            for pattern in shake_patterns:
                app_logger.info(f"Trying shake pattern: {pattern}")
                
                for values in pattern:
                    # Use the full adb shell command instead of emu
                    cmd = f"{CONFIG.adb['binary_path']} -s {device_id} shell \"setprop debug.sensors.accelerometer.x {values.split(':')[0]};" \
                        f"setprop debug.sensors.accelerometer.y {values.split(':')[1]};" \
                        f"setprop debug.sensors.accelerometer.z {values.split(':')[2]}\""
                    app_logger.debug(f"Executing: {cmd}")
                    subprocess.run(cmd, shell=True)
                    time.sleep(0.1)
                    
                # Reset to normal
                cmd = f"{CONFIG.adb['binary_path']} -s {device_id} shell \"setprop debug.sensors.accelerometer.x 0;" \
                    f"setprop debug.sensors.accelerometer.y 0;" \
                    f"setprop debug.sensors.accelerometer.z 9.81\""
                subprocess.run(cmd, shell=True)
                time.sleep(0.2)
                
            return True
                
        except Exception as e:
            app_logger.error(f"Error simulating shake: {e}")
            return False

    def type_text(self, text: str) -> None:
        print(f"[ADB] Typing text: '{text}' on device {self.device_id}")
        # subprocess.run(['adb', '-s', self.device_id, 'shell', 'input', 'text', text])

    def get_screen_size(self) -> tuple[int, int]:
        """Get device screen size"""
        try:
            result = subprocess.run(
                [CONFIG.adb["binary_path"], '-s', self.device_id, 'shell', 'wm', 'size'],
                capture_output=True, 
                text=True
            )
            match = re.search(r'(\d+)x(\d+)', result.stdout)
            if match:
                return int(match.group(1)), int(match.group(2))
            raise ValueError("Could not parse screen size")
        except Exception as e:
            raise RuntimeError(f"Failed to get screen size: {e}")

    def launch_package(self, package_name: str = CONFIG['adb']['package_name']):
        """Launch an app package"""
        subprocess.run(
            [CONFIG.adb["binary_path"], '-s', self.device_id, 'shell', 'monkey', '-p', package_name, '-c', 'android.intent.category.LAUNCHER', '1'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

    def force_stop_package(self, package_name: str = CONFIG['adb']['package_name']):
        """Force stop an app package"""
        subprocess.run([CONFIG.adb["binary_path"], '-s', self.device_id, 'shell', 'am', 'force-stop', package_name])

    def get_device_list(self) -> List[str]:
        """Get list of connected devices"""

        cmd = [CONFIG.adb["binary_path"], "version"]
        try:

            # We initially check the adb version to verify that everything is working
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=True,
                    shell=True
                )

            except (FileNotFoundError, subprocess.CalledProcessError):
                app_logger.error("ADB not found in PATH. Checking common Android SDK locations...")

                # Common SDK locations
                sdk_locations = [
                    os.path.expanduser("~/AppData/Local/Android/Sdk/platform-tools/adb.exe"),
                    "C:/Program Files/Android/platform-tools/adb.exe",
                    os.path.expanduser("~/Android/Sdk/platform-tools/adb.exe")
                ]

                for adb_path in sdk_locations:
                    if os.path.exists(adb_path):
                        app_logger.info(f"Found ADB at: {adb_path}")
                        cmd[0] = adb_path
                        CONFIG.adb["binary_path"] = adb_path
                        result = subprocess.run(
                            cmd,
                            capture_output=True,
                            text=True,
                            check=True,
                            shell=True
                        )
                        break
                else:
                    app_logger.error(
                        "ADB not found in common locations. Please ensure Android SDK platform-tools is installed")
                    return []

            lines = result.stdout.strip()
            version_re = re.compile("Version ([^\r\n]+)")
            version_match = version_re.search(lines)
            if version_match:
                adb_version = version_match.group(1)
                app_logger.debug(f"Found adb version: {adb_version}")
            else:
                app_logger.debug(f"Unknown adb version found:\n{lines}")

            if CONFIG.adb["enforce_connection"]:
                if CONFIG.adb['host'] and CONFIG.adb['port'] and CONFIG.adb['port'] > 0:
                    cmd = [CONFIG.adb["binary_path"], "connect", f"{CONFIG.adb['host']}:{CONFIG.adb['port']}"]
                    subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        check=True,
                        shell=True  # Required for Windows compatibility
                    )

            cmd = [CONFIG.adb["binary_path"], "devices"]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                shell=True  # Required for Windows compatibility
            )

            target_device = ""
            if CONFIG.adb['host'] and CONFIG.adb['port']:
                target_device = f"{CONFIG.adb['host']}:{CONFIG.adb['port']}"

            # Parse output and get device IDs
            lines = result.stdout.strip().split('\n')[1:]  # Skip first line
            devices = []
            for line in lines:
                if line.strip():
                    device_id = line.split()[0]
                    app_logger.debug(f"Found device: {device_id}")

                    if len(target_device) > 0:
                        if target_device in device_id:
                            devices.append(device_id)
                            break
                    else:
                        devices.append(device_id)

            return devices
                
        except Exception as e:
            app_logger.error(f"Error getting device list: {str(e)}")
            app_logger.debug(f"Full error details: {traceback.format_exc()}")
            return []

    def get_connected_device(self) -> Optional[str]:
        """Get the first connected device ID"""
        if (self.device_id):
            return self.device_id

        devices = self.get_device_list()
        if not devices:
            app_logger.error("No devices found. Please check:")
            app_logger.error("1. Device is connected via USB")
            app_logger.error("2. USB debugging is enabled")
            app_logger.error("3. Computer is authorized for USB debugging")
            return None
        if len(devices) > 1:
            app_logger.warning(f"Multiple devices found, using first one: {devices[0]}")
        return devices[0]

    def get_current_running_app(self) -> Optional[str]:
        """
        Returns the package name of the currently running app on the device.
        """
        try:
            result = subprocess.run(
                [CONFIG.adb["binary_path"], '-s', self.device_id, 'shell', 'dumpsys', 'window', 'windows'],
                capture_output=True,
                text=True,
                check=True
            )
            for line in result.stdout.splitlines():
                if 'mCurrentFocus' in line or 'mFocusedApp' in line:
                    package_name = line.split('/')[0].split()[-1]
                    app_logger.debug(f"Current running app: {package_name}")
                    return package_name
            return None
        
        except subprocess.CalledProcessError as e:
            app_logger.exception(f"Failed to get current running app: {e}")
            return None

    def take_screenshot(self) -> Optional[np.ndarray]:
        """
        Takes a screenshot directly into memory, decodes it into a NumPy array,
        returns the array, and initiates a non-blocking save to disk.
        Returns None on failure.
        """
        try:
            cmd = f"{CONFIG.adb['binary_path']} -s {self.device_id} " + 'exec-out "screencap -p 2>/dev/null"'
            
            result = subprocess.run(cmd, capture_output=True, text=False, check=False)

            if result.returncode != 0:
                error_output = result.stderr.decode(errors='replace').strip()
                if error_output:
                    app_logger.error(f"ADB command failed with return code {result.returncode}. Stderr: '{error_output}'")
                else:
                    app_logger.error(f"ADB command failed with return code {result.returncode}, but no stderr output.")
                return None

            screenshot_bytes = result.stdout
            
            if not screenshot_bytes:
                app_logger.error("No screenshot data (0 bytes) received from device, even though ADB command succeeded.")
                return None

            # --- Decode bytes to NumPy array ---
            np_bytes = np.frombuffer(screenshot_bytes, np.uint8)
            image_np = cv2.imdecode(np_bytes, cv2.IMREAD_COLOR)

            if image_np is None or image_np.size == 0:
                app_logger.error(f"Failed to decode screenshot bytes into an image (invalid image data?). Bytes received: {len(screenshot_bytes)}.")
                debug_filepath = Path("tmp") / "corrupted_screenshot_debug.bin"
                with open(debug_filepath, "wb") as f:
                    f.write(screenshot_bytes)
                app_logger.error(f"Raw received bytes (length {len(screenshot_bytes)}) saved to {debug_filepath} for inspection.")
                return None

            # --- Non-blocking save to disk ---
            ensure_dir("tmp")
            output_filepath = 'tmp/screen.png'
            file_save_executor.submit(self._save_image_to_disk_background, image_np, output_filepath)
            
            app_logger.debug(f"Screenshot captured and decoding process initiated. Saving to {output_filepath} in background.")
            self.cleanup_device_screenshots()

            return image_np

        except FileNotFoundError:
            app_logger.error(f"ADB binary not found at {CONFIG.adb['binary_path']}. Please ensure ADB is installed and in your PATH.")
            return None
        except Exception as e:
            app_logger.error(f"An unexpected error occurred during screenshot capture: {e}")
            return None
        
    def cleanup_device_screenshots(self) -> None:
        """Clean up screenshots from device"""
        try:
            cmd = f"{CONFIG.adb['binary_path']} -s {self.device_id} shell rm -f /sdcard/screen*.png"
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                app_logger.debug("Cleaned up device screenshots")
            else:
                app_logger.warning(f"Failed to clean device screenshots: {result.stderr}")
        except Exception as e:
            app_logger.error(f"Error cleaning device screenshots: {e}")

