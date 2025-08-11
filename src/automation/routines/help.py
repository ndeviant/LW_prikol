from src.automation.routines.routineBase import TimeCheckRoutine
from src.core.image_processing import find_template

class HelpRoutine(TimeCheckRoutine):
    # def __init__(self, device_id: str, interval: int, last_run: float = None, automation=None, *args, **kwargs):
    #     super().__init__(device_id, interval, last_run, automation, *args, **kwargs)
    #     self.helped_count: int = self.state.get('helped_count') or 0

    def _execute(self) -> bool:
        """Check and click help button if available"""
        return self.execute_with_error_handling(self._execute_internal)
        
    def _execute_internal(self) -> bool:
        if not find_template(
            "help",
            tap=True,
            error_msg="No help needed at this time",
            success_msg="Helping allies!"
        ):
            return True
            
        return True 