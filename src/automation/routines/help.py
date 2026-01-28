from src.automation.routines import FlexibleRoutine
from src.game import controls

class HelpRoutine(FlexibleRoutine):
    def _execute(self) -> bool:
        """Check and click help button if available"""
        return self.execute_with_error_handling(self._execute_internal)
        
    def _execute_internal(self) -> bool:
        if not controls.find_template(
            "help",
            tap=True,
            error_msg="No help needed at this time",
            success_msg="Helping allies!"
        ):
            return True
            
        return True 