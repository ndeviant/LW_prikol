from src.automation.routines.routineBase import TimeCheckRoutine
from src.core.logging import app_logger
from src.core.config import CONFIG
import time

from src.game.controls import launch_game, navigate_home

class ResetRoutine(TimeCheckRoutine):

    def _execute(self) -> bool:
        """Reset game state by restarting the app"""
        return self.execute_with_error_handling(self._execute_internal)
        
    def _execute_internal(self) -> bool:
        retry_count = 0
        while retry_count < CONFIG['max_home_attempts']:
            sleep_time = min(600, retry_count * 30)
            app_logger.info(f"Launching game in {sleep_time} seconds")
            time.sleep(sleep_time)
            if launch_game(self.device_id):
                app_logger.info("Game launched successfully")
                if navigate_home(self.device_id, force=True):
                    return True
        
        app_logger.error("Failed to navigate home after reset")
        return False 