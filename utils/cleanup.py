import os
import glob
from datetime import datetime, timedelta
from typing import List, Optional
from logging_config import app_logger
from .constants import PATHS
import shutil
import threading
import time
from pathlib import Path

class ResourceCleanup:
    def __init__(self, max_age_days: int = 7):
        self.max_age = timedelta(days=max_age_days)
        self.temp_dirs = [PATHS['TEMP_DIR'], PATHS['LOGS_DIR']]
        
    def cleanup_temp_files(self, file_patterns: Optional[List[str]] = None) -> None:
        """
        Clean up temporary files matching specified patterns.
        
        Args:
            file_patterns: List of file patterns to clean up (e.g., ['*.png', '*.log'])
        """
        if file_patterns is None:
            file_patterns = ['*.png', '*.log']
            
        current_time = datetime.now()
        
        for directory in self.temp_dirs:
            if not os.path.exists(directory):
                continue
                
            app_logger.info(f"Cleaning up directory: {directory}")
            
            for pattern in file_patterns:
                pattern_path = os.path.join(directory, pattern)
                for file_path in glob.glob(pattern_path):
                    try:
                        # Check file age
                        file_time = datetime.fromtimestamp(
                            os.path.getmtime(file_path)
                        )
                        if current_time - file_time > self.max_age:
                            os.remove(file_path)
                            app_logger.debug(f"Removed old file: {file_path}")
                    except Exception as e:
                        app_logger.error(f"Failed to remove file {file_path}: {e}")
    
    def cleanup_session_files(self) -> None:
        """Clean up temporary files created during the current session."""
        try:
            # Clean up ROI images
            roi_pattern = os.path.join(PATHS['TEMP_DIR'], 'roi_*.png')
            for file_path in glob.glob(roi_pattern):
                os.remove(file_path)
                app_logger.debug(f"Removed session file: {file_path}")
                
            # Clean up screenshots
            screenshot_pattern = os.path.join(PATHS['TEMP_DIR'], 'screenshot*.png')
            for file_path in glob.glob(screenshot_pattern):
                os.remove(file_path)
                app_logger.debug(f"Removed session file: {file_path}")
                
        except Exception as e:
            app_logger.error(f"Session cleanup failed: {e}")
    
    def __enter__(self) -> 'ResourceCleanup':
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.cleanup_session_files() 

def clear_tmp_folder():
    """Clear all files from the tmp folder"""
    try:
        # Clear tmp directory
        tmp_dir = Path('tmp')
        if tmp_dir.exists():
            shutil.rmtree(tmp_dir)
        tmp_dir.mkdir(exist_ok=True)
        app_logger.debug("Cleared tmp folder")
        
        # Clear old session directories
        sessions_dir = Path('sessions')
        if sessions_dir.exists():
            current_time = datetime.now()
            for session_dir in sessions_dir.iterdir():
                if session_dir.is_dir():
                    # Check directory age
                    dir_time = datetime.fromtimestamp(session_dir.stat().st_mtime)
                    if current_time - dir_time > timedelta(days=1):  # Keep sessions for 1 day
                        shutil.rmtree(session_dir)
                        app_logger.debug(f"Removed old session directory: {session_dir}")
                        
    except Exception as e:
        app_logger.error(f"Error during cleanup: {e}")

def periodic_cleanup():
    """Run cleanup every 5 minutes"""
    while True:
        time.sleep(300)  # 5 minutes
        app_logger.debug("Running periodic tmp folder cleanup")
        clear_tmp_folder()

def start_cleanup_thread():
    """Start the background cleanup thread"""
    cleanup_thread = threading.Thread(
        target=periodic_cleanup,
        daemon=True  # Thread will exit when main program exits
    )
    cleanup_thread.start()
    app_logger.debug("Started cleanup thread") 