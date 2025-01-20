from src.automation.routines.routineBase import TimeCheckRoutine
from src.core.adb import simulate_shake
from src.core.logging import app_logger
from src.core.config import CONFIG

class CollectResourcesRoutine(TimeCheckRoutine):

    def _execute(self) -> bool:
        """Reset game state by restarting the app"""
        return self.execute_with_error_handling(self._execute_internal)
        
    def _execute_internal(self) -> bool:
        print("Collecting resources todo")
        #simulate_shake(self.device_id)
        return True 