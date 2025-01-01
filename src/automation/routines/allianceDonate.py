from src.automation.routines import TimeCheckRoutine
from src.core.image_processing import find_and_tap_template

class AllianceDonateRoutine(TimeCheckRoutine):

    def _execute(self) -> bool:
        """Execute alliance donation sequence"""
        return self.execute_with_error_handling(self.navigate_and_donate)

    def navigate_and_donate(self) -> bool:
        """Navigate to the alliance donate menu and donate"""
        # Open alliance menu
        if not find_and_tap_template(
            self.device_id,
            "alliance",
            error_msg="Could not find alliance icon"
        ):
            return True
            
        # Click alliance tech icon
        if not find_and_tap_template(
            self.device_id,
            "alliance_tech_icon",
            error_msg="Could not find alliance tech icon"
        ):
            return True
            
        # Click recommended flag
        if not find_and_tap_template(
            self.device_id,
            "recommended_flag",
            error_msg="No recommended tech found"
        ):
            return True
            
        # Donate with long press
        if not find_and_tap_template(
            self.device_id,
            "donate_button",
            error_msg="No donate button found",
            long_press=True,
            press_duration=15.0
        ):
            return True
            
        return True