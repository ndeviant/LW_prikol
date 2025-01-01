from src.automation.routines.routineBase import TimeCheckRoutine
from src.core.image_processing import find_and_tap_template
from src.core.logging import app_logger
from src.core.config import CONFIG

class HelpRoutine(TimeCheckRoutine):
    def _execute(self) -> bool:
        """Check and click help button if available"""
        return self.execute_with_error_handling(self._execute_internal)
        
    def _execute_internal(self) -> bool:
        if not find_and_tap_template(
            self.device_id,
            "help",
            error_msg="No help needed at this time",
            success_msg="Helping allies!"
        ):
            return True
            
        return True 