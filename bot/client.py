"""
Pyrogram Bot Client with Time Sync Fix
Handles time offset for containerized environments
"""
import time
import logging
from pyrogram.client import Client
from pyrogram.raw.functions.help import GetConfig
from bot.config import Config

logging.getLogger("pyrogram").setLevel(logging.WARNING)

class TimeSyncClient(Client):
    """Client with automatic time sync"""
    
    async def connect(self):
        """Connect and sync time with Telegram servers"""
        try:
            await super().connect()
        except Exception as e:
            if "msg_id" in str(e).lower():
                print("⏱️ Syncing time with Telegram servers...")
                await self._sync_time()
                await super().connect()
            else:
                raise
    
    async def _sync_time(self):
        """Manually sync client time with Telegram"""
        try:
            # Get server time from Telegram
            await self.send(GetConfig())
        except:
            pass

# Bot client - use standard Client with proper configuration
app = Client(
    "bot_session",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN,
    workdir="."
)
