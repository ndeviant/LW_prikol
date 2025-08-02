from src.automation.routines.routineBase import DailyRoutine
from src.core.config import CONFIG
from src.core.image_processing import find_and_tap_template, wait_for_image
from src.game.device import controls
from src.core.logging import app_logger

class ApplyShield(DailyRoutine):
    shield_types = [8, 12, 24]

    def _execute(self) -> bool:
        """Check and click help button if available"""
        return self.execute_with_error_handling(self._execute_internal)
        
    def _execute_internal(self) -> bool:
        try:
            if not self.open_inventory():
                return False
            controls.human_delay('menu_animation')

            self.automation.game_state["is_home"] = False
            apllied_shield = None

            num_of_swipes = self.options.get("num_of_swipes", 3)
            for i in range(num_of_swipes):
                apllied_shield = self.click_one_of_shields()
                if apllied_shield:
                    break

                controls.swipe(direction="down", num_swipes=1)
                controls.human_delay('menu_animation')

            if not apllied_shield:
                app_logger.error(f"Failed to find any shield after doing: {num_of_swipes} swipes")
                return False

            if not find_and_tap_template(
                self.device_id,
                "use",
                error_msg=f"Could not find 'use' button",
                critical=True
            ):
                return False
            
            controls.human_delay('menu_animation')
            
            app_logger.info(f"Successfully applied {apllied_shield}h shield")
            return True
                    
        except Exception as e:
            app_logger.error(f"Error applying for a shield: {e}")
            return False
    
    def open_inventory(self) -> bool:
        """Open the profile menu"""
        try:
            if not find_and_tap_template(
                self.device_id,
                "inventory",
                error_msg=f"Could not find \"inventory\" button",
                critical=True
            ):
                return False

            return True
        
        except Exception as e:
            app_logger.error(f"Error opening inventory: {e}")
            return False

    def click_one_of_shields(self) -> int:
        shields = self.options.get("shields", [8])
        apllied_shield = None

        for shield_time in shields:
            if find_and_tap_template(
                self.device_id,
                f"shield_{shield_time}",
                error_msg=f"Failed to find shield_{shield_time} item",
                critical=True
            ):  
                apllied_shield = shield_time
                break

        return apllied_shield