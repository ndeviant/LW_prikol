from src.automation.routines import FlexibleRoutine
from src.game import controls
from src.core.logging import app_logger

class SnowStorm(FlexibleRoutine):
    def _execute(self) -> bool:
        """Check and click help button if available"""
        return self.execute_with_error_handling(self._execute_internal)
        
    def _execute_internal(self) -> bool:
        cold_wave_active = self.state.get('cold_wave_active', False)

        if (cold_wave_active):
            furnace_active = True
            self.state.set('furnace_active', furnace_active)

        furnace_active = self.state.get('furnace_active')

        """"""
        """ Turn off furnace if cold wave ended """
        """"""
        if not cold_wave_active and furnace_active:
            controls.human_delay('menu_animation')
            app_logger.info(f"Cold wave ended trying to turn the furnace off")
            
            self.swipe_down()

            if not self.open_furnace():
                self.swipe_up()
                return True
            
            self.automation.game_state["is_home"] = False
            controls.human_delay('menu_animation')
            
            if not controls.find_template(
                "s2_furnace_on",
                tap=True,
                tap_offset=(40, 0),
                error_msg=f"Could not find 'furnace_on' button",
                success_msg="Furnace turned off"
            ):
                controls.device.press_back()
                self.swipe_up()
                return True
            
            self.state.set('furnace_active', False)

            controls.human_delay('menu_animation')
            controls.device.press_back()
            self.swipe_up()
            controls.human_delay('menu_animation')

            return True
        """"""
        """"""
        """"""

        if not cold_wave_active:
            return True
                
        self.swipe_down()
        controls.human_delay('menu_animation')
        self.automation.game_state["is_home"] = False

        if not self.open_furnace():
            self.swipe_up()
            return True

        controls.human_delay('menu_animation')

        if not controls.find_template(
            "s2_furnace_on",
            tap=True,
            tap_offset=(40, 0),
            error_msg=f"Could not find 'furnace_on' button"
        ):
            controls.device.press_back()
            controls.human_delay('menu_animation')
            self.swipe_up()

            return True
        
        controls.human_delay('menu_animation')

        controls.find_template(
            "s2_furnace_off",
            tap=True,
            tap_offset=(40, 0),
            error_msg=f"Could not find 'furnace_on' button"
        )

        controls.human_delay('menu_animation')
        
        app_logger.info(f"Successfully turned furnace off and on")

        controls.device.press_back()
        controls.human_delay('menu_animation')
        self.swipe_up()
        controls.human_delay('menu_animation')
        return True
    
    def swipe_down(self):
        controls.device.swipe(start=("10%", "82%"), end=("10%", "32%"))  

    def swipe_up(self):
        controls.device.swipe(start=("10%", "32%"), end=("10%", "82%"))

    def open_furnace(self) -> bool:
        if not (controls.find_template(
            "s2_furnace_on_model",
            tap=True,
            wait=2,
            interval=0.5,
            error_msg=f"Could not find 's2_furnace_on_model' "
        ) or controls.find_template(
            "s2_furnace_off_model",
            tap=True,
            wait=2,
            interval=0.5,
            error_msg=f"Could not find 's2_furnace_off_model' "
        )):
            return False
        
        if not controls.find_template(
            "s2_btn_furnace",
            tap=True,
            wait=2,
            interval=0.25,
            error_msg=f"Could not find 's2_btn_furnace' "
        ):
            return False
        
        return True
