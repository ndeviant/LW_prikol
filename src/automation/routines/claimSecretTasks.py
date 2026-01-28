from src.automation.routines import FlexibleRoutine
from src.game import controls

class ClaimSecretTasks(FlexibleRoutine):
    def _execute(self) -> bool:
        """Check and click help button if available"""
        return self.execute_with_error_handling(self._execute_internal)
        
    def _execute_internal(self) -> bool:
        if not (controls.find_template(
            "tasks_claimable",
            tap=True,
            success_msg=f"Found 'tasks_claimable' button",
        ) or controls.find_template(
            "tasks_active",
            tap=True,
            success_msg=f"Found 'tasks_active' button",
        )):
            return True

        controls.human_delay('menu_animation')

        self.automation.game_state["is_home"] = False

        controls.find_template(
            "tasks_claim",
            tap=True,
            error_msg=f"Could not find 'tasks_claim' button",
        )
        
        return True


