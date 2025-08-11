from src.automation.routines.routineBase import DailyRoutine
from src.core.config import CONFIG
from src.core.image_processing import find_template
from src.game.device import controls
from src.core.logging import app_logger

class ApplyForSecretary(DailyRoutine):
    secretary_types = ["strategy", "security", "development", "science", "interior"]

    def _execute(self) -> bool:
        """Check and click help button if available"""
        return self.execute_with_error_handling(self._execute_internal)
        
    def _execute_internal(self) -> bool:
        if (not self.options.get("position")):
            app_logger.info(f"No secretary position was provided in `options.position`: {self.secretary_types}")
            return True

        self.automation.game_state["is_home"] = False

        self.open_profile_menu()
        if not find_template(
            "capitol_menu",
            tap=True,
            error_msg="Failed to find capitol menu",
            critical=True
        ):  
            return False
        
        controls.swipe(direction="down")
        controls.human_delay(CONFIG['timings']['menu_animation'])

        if not find_template(
            self.options.get("position"),
            tap=True,
            error_msg=f"Could not find {self.options.get("position")} secretary position",
            critical=True
        ):
            return False
                    
        controls.human_delay(CONFIG['timings']['menu_animation'])

        if not find_template(
            "apply",
            tap=True,
            error_msg=f"Could not find \"Apply\" button",
            critical=True
        ):
            return False

        return True 
                
    
    def open_profile_menu(self) -> bool:
        """Open the profile menu"""
        try:
            width, height = controls.get_screen_size()
            profile = CONFIG['ui_elements']['profile']
            profile_x = int(width * float(profile['x'].strip('%')) / 100)
            profile_y = int(height * float(profile['y'].strip('%')) / 100)
            controls.click(profile_x, profile_y)

            # Look for notification indicators
            notification = find_template(
                "awesome",
                wait=CONFIG['timings']['menu_animation'],
            )
            
            if notification:
                controls.click(notification[0], notification[1])
                controls.human_delay(CONFIG['timings']['menu_animation'])

            return True
        
        except Exception as e:
            app_logger.error(f"Error opening profile menu: {e}")
            return False
