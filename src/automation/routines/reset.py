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
        app_logger.info("Launching game")
        launch_game(self.device_id)
        navigate_home(self.device_id, force=True)
        retry_count = 0
        while retry_count < 3:
            if navigate_home(self.device_id, force=True):
                return True
            retry_count += 1
            time.sleep(2)
        
        app_logger.error("Failed to navigate home after reset")
        return False 