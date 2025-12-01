"""
Bot Command Handlers - Ultra Simple
"""
from pyrogram import filters
from pyrogram.types import Message
from bot.config import Config

def is_owner(_, __, message: Message):
    return message.from_user and message.from_user.id == Config.OWNER_ID

owner_filter = filters.create(is_owner)

def register_handlers(app):
    """Register all bot command handlers"""
    
    @app.on_message(filters.command("start") & owner_filter)
    async def start(client, message: Message):
        await message.reply(
            "🤖 **AutoRenamer Bot**\n\n"
            "Commands:\n"
            "/setsource <channel_id> - Set source channel\n"
            "/setdest <channel_id> - Set destination channel\n"
            "/process - Start processing\n"
            "/help - Show help"
        )
    
    @app.on_message(filters.command("help") & owner_filter)
    async def help_cmd(client, message: Message):
        await message.reply(
            "📖 **Help**\n\n"
            "/setsource - Set where to download from\n"
            "/setdest - Set where to upload to\n"
            "/process - Start file processing\n"
            "/status - Show current config"
        )
    
    @app.on_message(filters.command("status") & owner_filter)
    async def status(client, message: Message):
        await message.reply(
            f"📊 **Status**\n\n"
            f"Source Channels: {len(Config.SOURCE_CHANNEL_IDS)}\n"
            f"Destination Channels: {len(Config.DESTINATION_CHANNEL_IDS)}"
        )
    
    @app.on_message(filters.command("setsource") & owner_filter)
    async def set_source(client, message: Message):
        if len(message.command) < 2:
            await message.reply("Usage: /setsource <channel_id>")
            return
        
        channel_id = message.command[1]
        try:
            channel_id = int(channel_id)
            Config.SOURCE_CHANNEL_IDS = [channel_id]
            await message.reply(f"✅ Source channel set to: {channel_id}")
        except ValueError:
            await message.reply("❌ Invalid channel ID")
    
    @app.on_message(filters.command("setdest") & owner_filter)
    async def set_dest(client, message: Message):
        if len(message.command) < 2:
            await message.reply("Usage: /setdest <channel_id>")
            return
        
        channel_id = message.command[1]
        try:
            channel_id = int(channel_id)
            Config.DESTINATION_CHANNEL_IDS = [channel_id]
            await message.reply(f"✅ Destination channel set to: {channel_id}")
        except ValueError:
            await message.reply("❌ Invalid channel ID")
    
    @app.on_message(filters.command("process") & owner_filter)
    async def process(client, message: Message):
        if not Config.SOURCE_CHANNEL_IDS or not Config.DESTINATION_CHANNEL_IDS:
            await message.reply("❌ Please set source and destination channels first")
            return
        
        await message.reply("✅ Processing started (implementation pending)")
