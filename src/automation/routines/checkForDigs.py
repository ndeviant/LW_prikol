from src.automation.routines import TimeCheckRoutine
from src.core.logging import app_logger
from src.core.config import CONFIG
from src.core.image_processing import find_and_tap_template
from src.game.controls import navigate_home, human_delay
from src.core.discord_bot import DiscordNotifier
from discord import Embed
import asyncio
import os

class CheckForDigsRoutine(TimeCheckRoutine):
    def __init__(self, device_id: str, interval: int, last_run: float = None):
        super().__init__(device_id, interval, last_run)
        self.discord = DiscordNotifier()
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
                
            # Wait for chat to open
            human_delay(CONFIG['timings']['menu_animation'])
            
            # Navigate home again to ensure clean state
            if not navigate_home(self.device_id):
                app_logger.error("Failed to navigate home after clearing dig")
                return False
            
            # Send Discord notification
            asyncio.run(self.send_notification())
            return True
            
        except Exception as e:
            app_logger.error(f"Error in dig check routine: {e}")
            return False
            
    async def send_notification(self) -> bool:
        """Send bilingual notification"""
        if not self.is_enabled:
            return True
            
        dig_config = CONFIG['discord']['dig_notification']
        embed = Embed(color=int(dig_config['embed_color'], 16))
        embed.add_field(
            name=dig_config['embed_title'],
            value=dig_config['embed_value']
        )
        
        return await self.discord.send_notification(
            dig_config['content'],
            embed,
            username=CONFIG['discord'].get('bot_name', 'Game Bot')
        )
