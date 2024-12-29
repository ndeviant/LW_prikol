import subprocess
import threading
from typing import Optional
from src.core.config import CONFIG
from src.core.logging import app_logger

class NetworkCapture:
    def __init__(self, device_id: str):
        self.device_id = device_id
        self.process = None
        self.thread = None
        self.running = False

    def start(self):
        """Start capturing network traffic"""
        try:
            # Clear existing logs
            subprocess.run(['adb', '-s', self.device_id, 'logcat', '-c'])
            app_logger.info("Cleared existing logs")
            
            self.running = True
            
            def capture_logs():
                cmd = ['adb', '-s', self.device_id, 'logcat', '*:E', CONFIG['package_name']]
                app_logger.info(f"Starting logcat capture for {CONFIG['package_name']}")
                self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True)
                
                while self.running:
                    line = self.process.stdout.readline()
                    if not line:
                        break
                    
                    if CONFIG['package_name'] in line:
                        app_logger.debug(f"Captured log: {line.strip()}")
                        with open('tmp/network.log', 'a') as f:
                            f.write(f"{line}\n")
                            f.write("-" * 80 + "\n")
            
            self.thread = threading.Thread(target=capture_logs, daemon=True)
            self.thread.start()
            app_logger.info("Network capture thread started")
            return self
            
        except Exception as e:
            app_logger.error(f"Failed to start network capture: {e}")
            return None

    def stop(self):
        """Stop capturing network traffic"""
        self.running = False
        if self.process:
            self.process.terminate()
            self.process = None
        if self.thread:
            self.thread.join(timeout=1)
            self.thread = None
        app_logger.info("Network capture stopped")

def start_network_capture(device_id: str) -> Optional[NetworkCapture]:
    return NetworkCapture(device_id).start() 