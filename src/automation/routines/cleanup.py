from src.automation.routines import TimeCheckRoutine
from src.game.device import controls

class CleanupRoutine(TimeCheckRoutine):
    def _execute(self) -> bool:
        """Run cleanup tasks"""
        return self.execute_with_error_handling(self._execute_internal)
        
    def _execute_internal(self) -> bool:
        controls.cleanup_temp_files()
        controls.cleanup_device_screenshots()
        return True 