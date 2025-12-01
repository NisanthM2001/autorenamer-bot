import sys
from bot.config import Config
from bot.client import app
from bot.handlers import register_handlers
from bot.database import load_settings_sync

def load_settings_from_database():
    """Load all settings from database (MongoDB or memory)"""
    try:
        settings = load_settings_sync()
        Config.SOURCE_CHANNEL_IDS = settings.get("source_channels", [])
        Config.DESTINATION_CHANNEL_IDS = settings.get("destination_channels", [])
        Config.WHITELIST_WORDS = settings.get("whitelist_words", [])
        Config.BLACKLIST_WORDS = settings.get("blacklist_words", [])
        Config.REMOVED_WORDS = settings.get("removed_words", [])
        Config.FILE_PREFIX = settings.get("file_prefix", "")
        Config.FILE_SUFFIX = settings.get("file_suffix", "")
        Config.REMOVE_USERNAME = settings.get("remove_username", False)
        Config.CUSTOM_CAPTION = settings.get("custom_caption", "")
        Config.START_LINK = settings.get("start_link")
        Config.END_LINK = settings.get("end_link")
        Config.PROCESS_ABOVE_2GB = settings.get("process_above_2gb", False)
        Config.PARALLEL_DOWNLOADS = settings.get("parallel_downloads", 1)
    except Exception as e:
        print(f"⚠️ Could not load settings: {e}")

def main():
    print("=" * 50)
    print("Channel File Processor Bot")
    print("=" * 50)
    
    if not Config.is_configured():
        print("\nERROR: Bot is not configured!")
        print("\nPlease set the following environment variables:")
        print("  - API_ID: Your Telegram API ID")
        print("  - API_HASH: Your Telegram API Hash")
        print("  - BOT_TOKEN: Your bot token from @BotFather")
        print("  - OWNER_ID: Your Telegram user ID")
        print("\nGet API credentials from: https://my.telegram.org")
        print("=" * 50)
        sys.exit(1)
    
    # Load settings from database
    load_settings_from_database()
    
    info = Config.get_info()
    print(f"\nConfiguration status:")
    print(f"  - API: {'✅ OK' if info['api_configured'] else '❌ Missing'}")
    print(f"  - Bot Token: {'✅ OK' if info['bot_token_set'] else '❌ Missing'}")
    print(f"  - Source Channels: {info['source_channels']} configured")
    print(f"  - Destination Channels: {info['destination_channels']} configured")
    print(f"  - Whitelist: {len(info['whitelist_words'])} words")
    print(f"  - Blacklist: {len(info['blacklist_words'])} words")
    print()
    
    register_handlers(app)
    
    print("Starting bot...")
    print("=" * 50)
    
    app.run()

if __name__ == "__main__":
    main()
