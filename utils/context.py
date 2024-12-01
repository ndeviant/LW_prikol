from typing import Dict, Any, Optional
from logging_config import app_logger
from .device_utils import get_screen_size

class DeviceContext:
    """Manages device-specific context like screen dimensions"""
    _instance = None
    _screen_width: Optional[int] = None
    _screen_height: Optional[int] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DeviceContext, cls).__new__(cls)
        return cls._instance
    
    @classmethod
    def initialize(cls, device_id: str):
        """Initialize device context with screen dimensions"""
        if cls._screen_width is None or cls._screen_height is None:
            try:
                width, height = get_screen_size(device_id)
                cls._screen_width = width
                cls._screen_height = height
                app_logger.debug(f"Screen dimensions initialized: {width}x{height}")
            except Exception as e:
                app_logger.error(f"Failed to get screen dimensions: {e}")
                raise
    
    @classmethod
    def get_screen_dimensions(cls) -> tuple[int, int]:
        """Get current screen dimensions"""
        if cls._screen_width is None or cls._screen_height is None:
            raise RuntimeError("Device context not initialized. Call initialize() first.")
        return cls._screen_width, cls._screen_height
    
    @classmethod
    def reset(cls):
        """Reset the context (useful for testing)"""
        cls._screen_width = None
        cls._screen_height = None 