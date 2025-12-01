"""
AutoRenamer Bot - Simple Handlers
Ultra minimal bot for Koyeb
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
        await message.reply_text(
            "🤖 **AutoRenamer Bot**\n\n"
            "Commands:\n"
            "/setsource <channel_id> - Set source channel\n"
            "/setdest <channel_id> - Set destination channel\n"
            "/status - Show configuration\n"
            "/help - Show help"
        )
    
    @app.on_message(filters.command("help") & owner_filter)
    async def help_cmd(client, message: Message):
        await message.reply_text(
            "📖 **Help**\n\n"
            "**Commands:**\n"
            "/setsource <channel_id> - Set download source\n"
            "/setdest <channel_id> - Set upload destination\n"
            "/status - Show current configuration\n"
            "/process - Start processing (when configured)\n\n"
            "**Channel ID Format:**\n"
            "-100XXXXXXXXXX (for channels)\n"
            "@username (for public channels)"
        )
    
    @app.on_message(filters.command("status") & owner_filter)
    async def status(client, message: Message):
        src = len(Config.SOURCE_CHANNEL_IDS)
        dst = len(Config.DESTINATION_CHANNEL_IDS)
        await message.reply_text(
            f"📊 **Current Configuration**\n\n"
            f"Source Channels: {src}\n"
            f"Destination Channels: {dst}\n"
            f"Status: {'Ready to process' if src > 0 and dst > 0 else 'Not configured'}"
        )
    
    @app.on_message(filters.command("setsource") & owner_filter)
    async def set_source(client, message: Message):
        if len(message.command) < 2:
            await message.reply_text("Usage: /setsource <channel_id>")
            return
        
        try:
            channel_id = int(message.command[1])
            Config.SOURCE_CHANNEL_IDS = [channel_id]
            await message.reply_text(f"✅ Source channel set to: {channel_id}")
        except ValueError:
            await message.reply_text("❌ Invalid channel ID")
    
    @app.on_message(filters.command("setdest") & owner_filter)
    async def set_dest(client, message: Message):
        if len(message.command) < 2:
            await message.reply_text("Usage: /setdest <channel_id>")
            return
        
        try:
            channel_id = int(message.command[1])
            Config.DESTINATION_CHANNEL_IDS = [channel_id]
            await message.reply_text(f"✅ Destination channel set to: {channel_id}")
        except ValueError:
            await message.reply_text("❌ Invalid channel ID")
    
    @app.on_message(filters.command("process") & owner_filter)
    async def process_cmd(client, message: Message):
        if not Config.SOURCE_CHANNEL_IDS or not Config.DESTINATION_CHANNEL_IDS:
            await message.reply_text("❌ Please set source and destination channels first")
            return
        
        await message.reply_text(
            "✅ Processing started\n"
            "Implementation pending - will download and upload files"
        )
