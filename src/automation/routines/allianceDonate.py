from src.automation.routines import FlexibleRoutine
from src.core.image_processing import find_template
from src.game.device import controls
from src.core.config import CONFIG

class AllianceDonateRoutine(FlexibleRoutine):
    force_home: bool = True

    def _execute(self) -> bool:
        """Execute alliance donation sequence"""
        return self.execute_with_error_handling(self.navigate_and_donate)

    def navigate_and_donate(self) -> bool:
        self.automation.game_state["is_home"] = False

        """Navigate to the alliance donate menu and donate"""
        # Open alliance menu
        if not find_template(
            "alliance",
            tap=True,
            error_msg="Could not find alliance icon"
        ):
            return True
            
        controls.human_delay('menu_animation')

        # Click alliance tech icon
        if not find_template(
            "alliance_tech_icon",
            tap=True,
            error_msg="Could not find alliance tech icon"
        ):
            return True
            
        controls.human_delay('menu_animation')

        # Click recommended flag
        if not find_template(
            "recommended_flag",
            tap=True,
            error_msg="No recommended tech found"
        ):
            return True
            
        controls.human_delay('menu_animation')

        # Donate with long press
        if not find_template(
            "donate_button",
            tap=True,
            tap_duration=5.0,
            error_msg="No donate button found",
        ):
            return True
            
        return True