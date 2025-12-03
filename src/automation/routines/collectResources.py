from src.automation.routines import FlexibleRoutine
from src.core.logging import app_logger
from src.game import controls
from src.core.config import CONFIG

class CollectResourcesRoutine(FlexibleRoutine):
    def _execute(self) -> bool:
        """Reset game state by restarting the app"""
        return self.execute_with_error_handling(self._execute_internal)
    
    def use_rapid_prod(self):
        self.automation.game_state["is_home"] = False;
        controls.human_delay('menu_animation')

        controls.find_template(
            "rapid_production",
            tap=True,
            tap_offset=(0, 90)
        )
        controls.human_delay('menu_animation')
        controls.device.press_back()
        controls.human_delay('tap_delay')
        
    def _execute_internal(self) -> bool:
        for template in [
            "rss_exp",
            "rss_ore",
            "rss_screw",
            "rss_drone_box"
        ]:
            if controls.find_template(
                template,
                tap=True,
            ):
                controls.human_delay(0.2)
        
        if (controls.find_template("status_interior")):
            app_logger.info("Secretary of interior status found, collecting RSS")

            for template in [
                "rss_gold",
                "rss_iron",
                "rss_food",
            ]:
                controls.find_template(
                    template,
                    tap=True,
                )

            if controls.find_template(
                "skill_bubble",
                tap=True,
                wait=1,
                interval=0.4,
                success_msg=f"Found 'skill_bubble' icon"
            ):
                self.use_rapid_prod()
            elif controls.find_template(
                "profession",
                tap=True,
                wait=1,
                interval=0.4,
                success_msg=f"Found 'profession' icon"
            ):
                controls.human_delay('menu_animation')

                if controls.find_template(
                    "skills",
                    tap=True,
                    error_msg=f"Not found 'skills' icon"
                ):
                     self.use_rapid_prod()

        if not controls.find_template(
            "rss_truck",
            tap=True,
            error_msg="Could not find rss_truck icon",
        ):
            return True   

        controls.human_delay(CONFIG['timings']['menu_animation'])
        
        if not controls.find_template(
            "collect",
            tap=True,
            error_msg="Could not find collect icon",
        ):
            return True

        self.automation.game_state["is_home"] = False;

        return True 