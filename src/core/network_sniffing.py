import asyncio
import subprocess
import threading
import json
from datetime import datetime
from typing import Optional
from mitmproxy.proxy import server
from mitmproxy.options import Options
from mitmproxy.tools.dump import DumpMaster
from src.core.config import CONFIG
from src.core.logging import app_logger

class NetworkCapture:
    def __init__(self, device_id: str, proxy_port: int = 8082):
        self.device_id = device_id
        self.proxy_port = proxy_port
        self.process = None
        self.thread = None
        self.running = False
        self.master = None
        
    def capture_request(self, flow):
        """Callback for capturing requests"""
        try:
            # Only capture requests from our game package
            if CONFIG['package_name'] in flow.request.pretty_url:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                request_data = {
                    "timestamp": timestamp,
                    "url": flow.request.pretty_url,
                    "method": flow.request.method,
                    "headers": dict(flow.request.headers),
                    "content_type": flow.request.headers.get("Content-Type", ""),
                    "body": flow.request.text if flow.request.text else None
                }
                
                # Wait for response
                flow.reply()
                if flow.response:
                    request_data["response"] = {
                        "status_code": flow.response.status_code,
                        "headers": dict(flow.response.headers),
                        "body": flow.response.text if flow.response.text else None
                    }
                
                # Log the request/response
                with open('tmp/network.log', 'a') as f:
                    f.write(f"=== {timestamp} ===\n")
                    f.write(json.dumps(request_data, indent=2))
                    f.write("\n" + "=" * 80 + "\n")
                    
                app_logger.debug(f"Captured request to: {flow.request.pretty_url}")
                    
        except Exception as e:
            app_logger.error(f"Error capturing request: {e}")

    def start(self):
        """Start proxy server and configure device"""
        try:
            # Setup mitmproxy options
            opts = Options(
                listen_host='0.0.0.0',
                listen_port=self.proxy_port,
                mode=["regular"],
                ssl_insecure=True
            )
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            self.master = DumpMaster(opts, with_termlog=False, with_dumper=False)
            self.master.server = server.ProxyServer(opts)
            self.master.addons.add(self)
            
            # Configure device proxy
            subprocess.run([
                'adb', '-s', self.device_id, 'shell', 
                f'settings put global http_proxy 127.0.0.1:{self.proxy_port}'
            ])
            
            self.running = True
            
            def run_proxy():
                app_logger.info("Starting proxy server")
                asyncio.set_event_loop(loop)
                self.master.run()
                
            self.thread = threading.Thread(target=run_proxy, daemon=True)
            self.thread.start()
            app_logger.info("Network capture thread started")
            return self
            
        except Exception as e:
            app_logger.error(f"Failed to start network capture: {e}")
            return None

    def stop(self):
        """Stop capturing network traffic"""
        try:
            self.running = False
            if self.process:
                self.process.terminate()
                self.process = None

            if self.thread:
                self.thread = None

            # Pull capture file from device
            subprocess.run([
                'adb', '-s', self.device_id, 'pull',
                '/data/local/tmp/capture.pcap', 'tmp/capture.pcap'
            ])
            
            # Clean up capture file on device
            subprocess.run([
                'adb', '-s', self.device_id, 'shell',
                'rm /data/local/tmp/capture.pcap'
            ])
            
            app_logger.info("Network capture stopped")
            
        except Exception as e:
            app_logger.error(f"Error stopping network capture: {e}")

    def setup_certificates(self):
        """Setup mitmproxy certificates on device"""
        try:
            # Push cert to device
            subprocess.run([
                'adb', '-s', self.device_id, 'push',
                'cert/mitmproxy-ca-cert.cer', '/sdcard/'
            ])
            
            # Install cert
            subprocess.run([
                'adb', '-s', self.device_id, 'shell',
                'su -c "mount -o rw,remount /system && ' +
                'cp /sdcard/mitmproxy-ca-cert.cer /system/etc/security/cacerts/ && ' +
                'chmod 644 /system/etc/security/cacerts/mitmproxy-ca-cert.cer && ' +
                'mount -o ro,remount /system"'
            ])
            
            app_logger.info("Installed mitmproxy certificates")
            return True
            
        except Exception as e:
            app_logger.error(f"Failed to setup certificates: {e}")
            return False

def start_network_capture(device_id: str) -> Optional[NetworkCapture]:
    return NetworkCapture(device_id).start() 