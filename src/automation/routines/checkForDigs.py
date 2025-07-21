from src.automation.routines import TimeCheckRoutine
from src.core.logging import app_logger
from src.core.image_processing import find_and_tap_template, wait_for_image
from src.core.discord_bot import discord
from src.game.controls import human_delay, humanized_tap, handle_swipes
from src.core.config import CONFIG
from src.core.adb import get_screen_size, press_back
import asyncio
import os

class CheckForDigsRoutine(TimeCheckRoutine):
    def __init__(self, device_id: str, interval: int, last_run: float = None, automation=None, **kwargs):
        super().__init__(device_id, interval, last_run, automation, **kwargs)
        self.is_enabled_notification = bool(os.getenv('DISCORD_WEBHOOK_URL'))
        self.unclaimed_dig: bool = False
        self.claimed_count: int = 0

        if not self.is_enabled_notification:
            app_logger.warning("Dig notification routine disabled: DISCORD_WEBHOOK_URL not found in environment variables")
        
    def _execute(self) -> bool:
        """Execute dig notification check sequence"""
        return self.execute_with_error_handling(self._execute_internal)
        
    def _execute_internal(self) -> bool:
        """Check for dig icon and handle if found"""
        try:
            if (self.unclaimed_dig):
                self.search_chat_for_digs()

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

            if not self.options.get("auto_claim"):
                return True

            # Check if dig is already dug up
            app_logger.info(f"Attempting to claim dig automatically")
            self.claim_dig_from_chat()

            # If we just start digging
            if not (find_and_tap_template(
                self.device_id,
                "dig_chat_start",
                error_msg="Could not find dig_chat_start icon",
            ) or find_and_tap_template(
                self.device_id,
                "dig_chat_start_drone",
                error_msg="Could not find dig_chat_start_drone icon",
            )):
                return True
            
            self.unclaimed_dig = True
            
            human_delay(CONFIG['timings']['menu_animation'])
            human_delay(CONFIG['timings']['rally_animation'])

            if not (find_and_tap_template(
                self.device_id,
                "dig_dig",
                success_msg="Found dig_dig icon",
                error_msg="Could not find dig_dig icon",
            ) or find_and_tap_template(
                self.device_id,
                "dig_dig_exc",
                success_msg="Found dig_dig_exc icon",
                error_msg="Could not find dig_dig_exc icon",
                offset=(0, -40)
            ) or find_and_tap_template(
                self.device_id,
                "dig_dig_drone",
                success_msg="Found dig_dig_drone icon",
                error_msg="Could not find dig_dig_drone icon",
                offset=(0, -15)
            )):
                return True
            
            human_delay(CONFIG['timings']['rally_animation'])

            if not (find_and_tap_template(
                self.device_id,
                "dig_dig_dig",
                error_msg="Could not find dig_dig_dig icon",
            ) or find_and_tap_template(
                self.device_id,
                "dig_dig_dig_drone",
                error_msg="Could not find dig_dig_dig_drone icon",
            )):
                return True
            
            human_delay(CONFIG['timings']['menu_animation'])
            
            if not find_and_tap_template(
                self.device_id,
                "march",
                error_msg="Could not find dig march icon",
            ):
                return True
            
            if not self.options.get("wait_for_dig"):
                return True
            
            claim_btn = wait_for_image(
                self.device_id,
                "dig_claim",
                timeout=self.options.get("wait_for_dig", 60),
                interval=0.5
            )

            if claim_btn:
                self.unclaimed_dig = False
                humanized_tap(self.device_id, claim_btn[0], claim_btn[1])
                self.claimed_count += 1
                app_logger.info(f"Dig claimed, total count: {self.claimed_count}")

            return True
            
        except Exception as e:
            app_logger.error(f"Error in dig check routine: {e}")
            return False
        
    def open_alli_chat(self, device_id: str) -> bool:
        """Open the alliance chat"""
        try:
            width, height = get_screen_size(device_id)
            chat = CONFIG['ui_elements']['chat']
            chat_x = int(width * float(chat['x'].strip('%')) / 100)
            chat_y = int(height * float(chat['y'].strip('%')) / 100)
            humanized_tap(device_id, chat_x, chat_y)
            human_delay(CONFIG['timings']['menu_animation'])

            # Check if alliance chat is not selected
            alli_chat_inactive = wait_for_image(
                device_id,
                "alliance_chat_inactive",
                timeout=CONFIG['timings']['menu_animation'],
            )
            
            if alli_chat_inactive:
                humanized_tap(device_id, alli_chat_inactive[0], alli_chat_inactive[1])
                human_delay(CONFIG['timings']['menu_animation'])

            return True
        
        except Exception as e:
            app_logger.error(f"Error opening alli chat: {e}")
            return False

    def claim_dig_from_chat(self) -> bool:
        # Check if dig is available to claim in chat
        if (find_and_tap_template(
            self.device_id,
            "dig_chat_claim",
            success_msg="Found dig_chat_claim icon",
            offset=(0, 15)
        ) or find_and_tap_template(
            self.device_id,
            "dig_chat_claim_drone",
            success_msg="Found dig_chat_claim_drone icon",
            offset=(0, 15)
        )):
            human_delay(CONFIG['timings']['rally_animation'])

            if find_and_tap_template(
                    self.device_id,
                    "dig_claim",
                    error_msg="Could not find dig_claim icon",
                    success_msg="Found dig_claim icon"
                ):
                self.claimed_count += 1
                app_logger.info(f"Dig claimed, total count: {self.claimed_count}")

            self.unclaimed_dig = False

            return True
        
        return False
    
            
    def search_chat_for_digs(self) -> bool:
        app_logger.info(f"Searching chat for digs")
        self.automation.game_state["is_home"] = False;
        self.open_alli_chat(self.device_id)

        chat_search_swipes = self.options.get("chat_search_swipes", 5);

        if self.claim_dig_from_chat():
            return True
        for _ in range(chat_search_swipes):
            handle_swipes(self.device_id, direction="up", num_swipes=1)
            human_delay(CONFIG['timings']['menu_animation'])
            if self.claim_dig_from_chat():
                return True

        app_logger.info(f"No unclaimed dig found in chat")
        self.unclaimed_dig = False
        
        return True
            
    async def send_notification(self) -> bool:
        """Send bilingual notification"""
        if not self.is_enabled_notification:
            return True
            
        return await discord.send('dig')
