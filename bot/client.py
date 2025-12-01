"""
Pyrogram Bot Client with Time Sync
"""
from pyrogram.client import Client
from bot.config import Config

# Bot client only
app = Client(
    "bot_session",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN,
    workdir=".",
    in_memory=True  # Keep session in memory for Koyeb
)
