from src.automation.routines import TimeCheckRoutine
from src.core.logging import app_logger
from src.core.image_processing import find_and_tap_template, wait_for_image
from src.core.discord_bot import discord
from src.game.controls import human_delay, humanized_tap
from src.core.config import CONFIG
import asyncio
import os

class CheckForDigsRoutine(TimeCheckRoutine):
    def __init__(self, device_id: str, interval: int, last_run: float = None, automation=None, **kwargs):
        super().__init__(device_id, interval, last_run, automation, **kwargs)
        self.is_enabled = bool(os.getenv('DISCORD_WEBHOOK_URL'))
        if not self.is_enabled:
            app_logger.warning("Dig notification routine disabled: DISCORD_WEBHOOK_URL not found in environment variables")
        
    def _execute(self) -> bool:
        """Execute dig notification check sequence"""
        if not self.is_enabled:
            return True
        return self.execute_with_error_handling(self._execute_internal)
        
    def _execute_internal(self) -> bool:
        """Check for dig icon and handle if found"""
        try:
            # Open chat by clicking the dig icon
            if not find_and_tap_template(
                self.device_id,
                "dig",
                error_msg="Could not find dig icon",
                success_msg="Found dig icon"
            ):
                return True
            
            self.automation.game_state["is_home"] = False;
                
            # Send Discord notification
            asyncio.run(self.send_notification())

            app_logger.info(f"Attempting to claim dig automatically")

            # Check if dig is available to claim
            if (find_and_tap_template(
                self.device_id,
                "dig_chat_claim",
                error_msg="Could not find dig_chat_claim icon",
                success_msg="Found dig_chat_claim icon"
            ) or find_and_tap_template(
                self.device_id,
                "dig_chat_claim_drone",
                error_msg="Could not find dig_chat_claim_drone icon",
                success_msg="Found dig_chat_claim_drone icon"
            )):
                human_delay(CONFIG['timings']['rally_animation'])

                find_and_tap_template(
                    self.device_id,
                    "dig_claim",
                    error_msg="Could not find dig_claim icon",
                    success_msg="Found dig_claim icon"
                )

                return True
            
            # If only starts dig
            if not find_and_tap_template(
                self.device_id,
                "dig_chat_start",
                error_msg="Could not find dig_chat_start icon",
            ):
                return True
            
            human_delay(CONFIG['timings']['rally_animation'])

            if not find_and_tap_template(
                self.device_id,
                "dig_dig",
                error_msg="Could not find dig_dig icon",
            ):
                return True
            
            claim_btn = wait_for_image(
                self.device_id,
                "dig_claim",
                timeout=60,
                interval=0.5
            )
            
            if claim_btn:
                humanized_tap(self.device_id, claim_btn[0], claim_btn[1])
            
            return True
            
        except Exception as e:
            app_logger.error(f"Error in dig check routine: {e}")
            return False
            
    async def send_notification(self) -> bool:
        """Send bilingual notification"""
        if not self.is_enabled:
            return True
            
        return await discord.send('dig')
