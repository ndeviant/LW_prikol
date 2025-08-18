from src.automation.routines import FlexibleRoutine
from src.game import controls

class AllianceGiftsRoutine(FlexibleRoutine):
    force_home: bool = True

    def _execute(self) -> bool:
        """Execute alliance donation sequence"""
        return self.execute_with_error_handling(self.collect_gifts)

    def collect_gifts(self) -> bool:
        self.automation.game_state["is_home"] = False

        """Navigate to the alliance donate menu and donate"""
        # Open alliance menu
        if not controls.find_template(
            "alliance",
            tap=True,
            error_msg="Could not find alliance icon"
        ):
            return True
            
        controls.human_delay('menu_animation')

        # Click alliance gifts icon
        if not controls.find_template(
            "alliance_gifts",
            tap=True,
            error_msg="Could not find alliance_gifts icon"
        ):
            return True
        
        controls.human_delay('menu_animation')

        # Click collect all button
        if controls.find_template(
            "alliance_claim_all",
            tap=True,
            error_msg="No claim all button found"
        ):
            # Clear claim message
            controls.human_delay(2)
            controls.device.press_back()
            controls.human_delay(1)
        
        # Open premium tab
        if not controls.find_template(
            "alliance_gift_premium",
            tap=True,
            error_msg="No premium tab found found"
        ):
            return True
        
        controls.human_delay('menu_animation')

        # Click collect all button
        controls.find_template(
            "alliance_claim_all",
            tap=True,
            error_msg="No claim all button found"
        )
        
        return True