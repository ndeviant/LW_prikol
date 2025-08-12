from pathlib import Path
from typing import Optional
from src.core.logging import app_logger
from src.game.device import controls

class CleanupManager:
    _instance: Optional['CleanupManager'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self.cleanup_handlers = []
            self.device_id = None
            self.skip_cleanup = False
    
    def set_device(self, device_id: str):
        """Set the device ID for cleanup"""
        self.device_id = device_id
    
    def set_skip_cleanup(self, skip: bool):
        """Set whether to skip cleanup on exit"""
        self.skip_cleanup = skip
    
    def register_cleanup(self, handler):
        """Register a cleanup handler"""
        if handler not in self.cleanup_handlers:
            self.cleanup_handlers.append(handler)
    
    def cleanup(self):
        """Run cleanup tasks if not skipped"""
        if self.skip_cleanup:
            app_logger.info("Skipping cleanup as requested")
            return
            
        if not self.device_id:
            return
            
        try:
            app_logger.info("Running cleanup tasks...")
            controls.cleanup_temp_files()
            controls.cleanup_device_screenshots()
        except Exception as e:
            app_logger.error(f"Error during cleanup: {e}") 