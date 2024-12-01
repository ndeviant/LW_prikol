from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any, Generator
import json
import uuid
import os
from contextlib import contextmanager

from logging_config import app_logger
from .config_validation import Config
from .cleanup import ResourceCleanup
from .error_handling import GameAutomationError

@dataclass
class SessionStats:
    """Statistics for the current session"""
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    total_secretaries: int = 0
    processed_secretaries: int = 0
    successful_accepts: int = 0
    errors: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert stats to dictionary for serialization"""
        return {
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "total_secretaries": self.total_secretaries,
            "processed_secretaries": self.processed_secretaries,
            "successful_accepts": self.successful_accepts,
            "errors": self.errors,
            "duration": str(self.end_time - self.start_time) if self.end_time else None
        }

class Session:
    """Manages application session state and resources"""
    
    def __init__(
        self,
        config: Config,
        device_id: str,
        session_dir: str = "sessions"
    ):
        self.session_id = str(uuid.uuid4())
        self.config = config
        self.device_id = device_id
        self.stats = SessionStats()
        self.session_dir = Path(session_dir)
        self.session_path = self.session_dir / self.session_id
        self.cleanup = ResourceCleanup()
        
        # Create session directory
        self.session_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize session log
        self._init_session_log()
    
    def _init_session_log(self):
        """Initialize session logging"""
        log_path = self.session_path / "session.log"
        app_logger.info(f"Session {self.session_id} started")
        app_logger.info(f"Session log: {log_path}")
    
    def save_screenshot(self, name: str, image_path: str):
        """Save a screenshot to the session directory"""
        if not image_path or not os.path.exists(image_path):
            return
            
        screenshot_dir = self.session_path / "screenshots"
        screenshot_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_path = screenshot_dir / f"{name}_{timestamp}.png"
        
        try:
            os.rename(image_path, new_path)
            app_logger.debug(f"Saved screenshot: {new_path}")
        except Exception as e:
            app_logger.error(f"Failed to save screenshot: {e}")
    
    def record_error(self, error: Exception, context: str = ""):
        """Record an error in the session"""
        self.stats.errors += 1
        error_log = {
            "timestamp": datetime.now().isoformat(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context
        }
        
        error_log_path = self.session_path / "errors.json"
        try:
            if error_log_path.exists():
                with open(error_log_path, 'r') as f:
                    errors = json.load(f)
            else:
                errors = []
            
            errors.append(error_log)
            
            with open(error_log_path, 'w') as f:
                json.dump(errors, f, indent=2)
        except Exception as e:
            app_logger.error(f"Failed to log error: {e}")
    
    def update_stats(self, **kwargs):
        """Update session statistics"""
        for key, value in kwargs.items():
            if hasattr(self.stats, key):
                setattr(self.stats, key, value)
    
    def save_session_info(self):
        """Save session information and statistics"""
        self.stats.end_time = datetime.now()
        
        session_info = {
            "session_id": self.session_id,
            "device_id": self.device_id,
            "stats": self.stats.to_dict(),
            "config": {
                "debug": self.config.options.debug,
                "templates_used": list(self.config.templates.secretaries.keys())
            }
        }
        
        try:
            with open(self.session_path / "session_info.json", 'w') as f:
                json.dump(session_info, f, indent=2)
        except Exception as e:
            app_logger.error(f"Failed to save session info: {e}")
    
    def cleanup_session(self):
        """Clean up session resources"""
        try:
            self.cleanup.cleanup_session_files()
            app_logger.info(f"Session {self.session_id} cleaned up")
        except Exception as e:
            app_logger.error(f"Session cleanup failed: {e}")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.record_error(exc_val)
        self.save_session_info()
        self.cleanup_session()

@contextmanager
def create_session(config: Config, device_id: str) -> Generator[Session, None, None]:
    """Context manager for creating and managing a session"""
    session = None
    try:
        session = Session(config, device_id)
        yield session
    except Exception as e:
        if session:
            session.record_error(e, "Session initialization")
        raise GameAutomationError(f"Session failed: {e}")
    finally:
        if session:
            session.save_session_info()
            session.cleanup_session() 