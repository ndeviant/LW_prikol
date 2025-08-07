from src.automation.routines.routineBase import TimeCheckRoutine
from src.core.config import CONFIG
from src.core.image_processing import find_and_tap_template, find_template
from src.game.device import controls
from src.core.logging import app_logger

class CheckAnotherDeviceRoutine(TimeCheckRoutine):
    def _execute(self) -> bool:
        """Check and click help button if available"""
        return self.execute_with_error_handling(self._execute_internal)
        
    def _execute_internal(self) -> bool:
        return not self.check_active_on_another_device() 
    
    def check_active_on_another_device(self) -> bool:
        """Find another device popup"""
        try:
            app_logger.debug("Checking if account is active on another device")
            # Check if notification is on
            notification = find_template(self.device_id, "another_device")
            if notification:
                total_wait_time = CONFIG['timings']['another_device_wait'] or 300

                app_logger.info(f"Account is active on another device, waiting for {total_wait_time}s")

                # The progress step (20% of the total time)
                step_duration = total_wait_time * 0.20
                remaining_time = total_wait_time

                # Loop to show progress
                for i in range(1, 6): # This will loop 5 times for 20%, 40%, 60%, 80%, 100%
                    controls.human_delay(step_duration, multiplier=1.0) # Assuming human_delay takes the duration
                    remaining_time -= step_duration

                    app_logger.info(f"App will be restarted. Time remaining: {remaining_time:.1f}s")
                    
                # The full delay is now complete
                
                controls.cleanup_temp_files()
                controls.force_stop_package()

                return True
            
            return False
                
        except Exception as e:
            app_logger.error(f"Error check_active_on_another_device: {e}")
            return False