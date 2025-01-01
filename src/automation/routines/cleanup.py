from src.automation.routines import TimeCheckRoutine
from src.core.logging import app_logger
from src.core.device import cleanup_temp_files, cleanup_device_screenshots

class CleanupRoutine(TimeCheckRoutine):
    def _execute(self) -> bool:
        """Run cleanup tasks"""
        return self.execute_with_error_handling(self._execute_internal)
        
    def _execute_internal(self) -> bool:
        cleanup_temp_files()
        cleanup_device_screenshots(self.device_id)
        return True 