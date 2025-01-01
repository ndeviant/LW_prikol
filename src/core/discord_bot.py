from discord import Webhook, Embed
from dotenv import load_dotenv
import os
import aiohttp
from src.core.logging import app_logger

load_dotenv()

class DiscordNotifier:
    def __init__(self):
        self.webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
        
    async def send_notification(self, content: str, embeds: list = None, username: str = "Game Bot") -> bool:
        """Send notification to Discord webhook"""
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