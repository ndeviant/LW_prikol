from typing import Optional, Type
import traceback
from logging_config import app_logger

class GameAutomationError(Exception):
    """Base exception class for game automation errors."""
    def __init__(self, message: str, cause: Optional[Exception] = None):
        super().__init__(message)
        self.cause = cause
        self.log_error()
    
    def log_error(self):
        """Log the error with its traceback if available."""
        error_message = str(self)
        if self.cause:
            error_message += f"\nCaused by: {type(self.cause).__name__}: {str(self.cause)}"
            error_message += f"\nTraceback:\n{''.join(traceback.format_tb(self.cause.__traceback__))}"
        app_logger.error(error_message)

class DeviceError(GameAutomationError):
    """Raised when there are issues with the Android device."""
    pass

class ImageProcessingError(GameAutomationError):
    """Raised when there are issues with image processing."""
    pass

class OCRError(GameAutomationError):
    """Raised when there are issues with OCR processing."""
    pass

class ConfigurationError(GameAutomationError):
    """Raised when there are issues with configuration."""
    pass

def handle_error(error: Exception, context: str = "") -> GameAutomationError:
    """Convert any exception to a GameAutomationError with context."""
    if isinstance(error, GameAutomationError):
        return error
        
    message = f"Error during {context}: {str(error)}" if context else str(error)
    return GameAutomationError(message, cause=error) 