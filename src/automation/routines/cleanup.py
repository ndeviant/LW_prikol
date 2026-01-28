from src.automation.routines import FlexibleRoutine
from src.game import controls

class CleanupRoutine(FlexibleRoutine):
    def _execute(self) -> bool:
        """Run cleanup tasks"""
        return self.execute_with_error_handling(self._execute_internal)
        
    def _execute_internal(self) -> bool:
        controls.device.cleanup_temp_files()
        controls.device.cleanup_device_screenshots()
        return True 