import sys
from bot.config import Config
from bot.client import app
from bot.handlers import register_handlers

def main():
    print("=" * 50)
    print("AutoRenamer Bot - Simple Edition")
    print("=" * 50)
    
    if not Config.is_configured():
        print("\nERROR: Bot not configured!")
        print("Bot credentials hardcoded in bot/config.py")
        sys.exit(1)
    
    info = Config.get_info()
    print(f"\nConfiguration status:")
    print(f"  - Telegram API: {'✅ OK' if info['api_configured'] else '❌ Missing'}")
    print(f"  - Bot Token: {'✅ OK' if info['bot_token_set'] else '❌ Missing'}")
    print(f"  - Owner ID: {'✅ OK' if info['owner_id_set'] else '❌ Missing'}")
    print()
    print("Starting bot...")
    print("=" * 50)
    print("✅ Bot is running!")
    print("📌 No database - settings only stored in current session")
    print("=" * 50)
    
    register_handlers(app)
    app.run()

if __name__ == "__main__":
    main()
