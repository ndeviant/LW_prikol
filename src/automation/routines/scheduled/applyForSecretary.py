from src.automation.routines.routineBase import DailyRoutine
from src.core.adb import press_back
from src.core.config import CONFIG
from src.core.device import get_screen_size
from src.core.image_processing import find_and_tap_template, wait_for_image
from src.game.controls import handle_swipes, human_delay, humanized_tap
from src.core.logging import app_logger

class ApplyForSecretary(DailyRoutine):
    secretary_types = ["strategy", "security", "development", "science", "interior"]

    def _execute(self) -> bool:
        """Check and click help button if available"""
        return self.execute_with_error_handling(self._execute_internal)
        
    def _execute_internal(self) -> bool:
        try:
            if (not self.options.get("position")):
                app_logger.info(f"No secretary position was provided in `options.position`: {self.secretary_types}")
                return True

            self.automation.game_state["is_home"] = False

            self.open_profile_menu()
            if not find_and_tap_template(
                self.device_id,
                "capitol_menu",
                error_msg="Failed to find capitol menu",
                critical=True
            ):  
                return False
            
            handle_swipes(self.device_id, direction="down", num_swipes=1)
            human_delay(CONFIG['timings']['menu_animation'])

            if not find_and_tap_template(
                self.device_id,
                self.options.get("position"),
                error_msg=f"Could not find {self.options.get("position")} secretary position",
                critical=True
            ):
                return False
                        
            human_delay(CONFIG['timings']['menu_animation'])

            if not find_and_tap_template(
                self.device_id,
                "apply",
                error_msg=f"Could not find \"Apply\" button",
                critical=True
            ):
                return False

            return True 
                    
        except Exception as e:
            app_logger.error(f"Error applying for a secretary position: {e}")
            return False
    
    def open_profile_menu(self) -> bool:
        device_id = self.device_id
        """Open the profile menu"""
        try:
            width, height = get_screen_size(device_id)
            profile = CONFIG['ui_elements']['profile']
            profile_x = int(width * float(profile['x'].strip('%')) / 100)
            profile_y = int(height * float(profile['y'].strip('%')) / 100)
            humanized_tap(device_id, profile_x, profile_y)

            # Look for notification indicators
            notification = wait_for_image(
                device_id,
                "awesome",
                timeout=CONFIG['timings']['menu_animation'],
            )
            
            if notification:
                humanized_tap(device_id, notification[0], notification[1])
                press_back(device_id)
                human_delay(CONFIG['timings']['menu_animation'])

            return True
        
        except Exception as e:
            app_logger.error(f"Error opening profile menu: {e}")
            return False
