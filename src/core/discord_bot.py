from discord import Webhook, Embed
from dotenv import load_dotenv
import os
import aiohttp
from src.core.logging import app_logger
from src.core.config import CONFIG

load_dotenv()

class DiscordNotifier:
    def __init__(self):
        self.webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
        self.is_enabled = bool(os.getenv('DISCORD_WEBHOOK_URL'))
        
        if not self.is_enabled:
            app_logger.warning("Notification routine disabled: DISCORD_WEBHOOK_URL not found in environment variables")

    async def send(self, template: str) -> bool:
        this_config = CONFIG['discord']['notifications'][template]
        embed = Embed(color=int(this_config['embed_color'], 16))
        embed.add_field(
            name=this_config['embed_title'] or '',
            value=this_config['embed_value']
        )
        return await self.send_notification(   
            this_config['content'],
            embed,
            username=CONFIG['discord'].get('bot_name', 'Game Bot')
        )
        
    async def send_notification(self, content: str, embeds: list = None, username: str = "Game Bot") -> bool:
        """Send notification to Discord webhook"""
        if not self.is_enabled:
            return True
        
        try:
            if not self.webhook_url:
                app_logger.error("Discord webhook URL not configured")
                return False
                
            async with aiohttp.ClientSession() as session:
                webhook = Webhook.from_url(self.webhook_url, session=session)
                await webhook.send(
                    content=content,
                    embeds=embeds if isinstance(embeds, list) else [embeds] if embeds else None,
                    username=username
                )
            return True
            
        except Exception as e:
            app_logger.error(f"Failed to send Discord notification: {e}")
            return False
        
discord = DiscordNotifier()
