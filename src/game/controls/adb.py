import os
from random import random
import re
import subprocess
import traceback
from typing import List, Optional

from src.core.config import CONFIG
from src.core.logging import app_logger
from src.game.controls.strategy import ControlStrategy

# 2. Concrete Strategies
class ADBControls(ControlStrategy):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.device_id = self.get_connected_device()

    @property
    def is_app_running(self) -> bool:
        # Check if game is running first
        current_app = self.get_current_running_app()
        if current_app == CONFIG['package_name']:
            return True

    """
    A Concrete Strategy for controlling a device via ADB commands.
    """
    def _perform_click(self, x: int, y: int, duration: float) -> bool:
        """Execute a long press at coordinates with specified duration
        
        Args:
            device_id: Device identifier
            x: X coordinate
            y: Y coordinate
            duration: Press duration in milliseconds
        """
        
        device_id: str = self.device_id

        try:
            cmd = f"{CONFIG.adb['binary_path']} -s {device_id} shell input swipe {x} {y} {x} {y} {duration}"
            subprocess.run(cmd, shell=True, check=True)
            return True
        
        except subprocess.CalledProcessError:
            app_logger.error(f"Failed to execute long press on device {device_id}")
            return False

    def _perform_swipe(self, start_x: int, start_y: int, end_x: int, end_y: int, duration: int = 300) -> bool:
        """Swipe screen from start to end coordinates"""
        try:
            cmd = f"{CONFIG.adb['binary_path']} -s {self.device_id} shell input swipe {start_x} {start_y} {end_x} {end_y} {duration}"
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

    def simulate_shake(self) -> None:
        print(f"[ADB] Simulating shake gesture on device {self.device_id}")
        # ADB does not have a direct 'shake' command, might involve complex sequence or specific emulator features.
        # This is a placeholder for demonstration.

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

    def launch_package(self, package_name: str = CONFIG['package_name']):
        """Launch an app package"""
        subprocess.run(
            [CONFIG.adb["binary_path"], '-s', self.device_id, 'shell', 'monkey', '-p', package_name, '-c', 'android.intent.category.LAUNCHER', '1'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

    def force_stop_package(self, package_name: str = CONFIG['package_name']):
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

        devices = self.get_device_list()
        if not devices:
            app_logger.error("No devices connected")
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