"""
AutoRenamer Bot - Main Entry Point with Time Sync
"""
import sys
import time
import asyncio
from bot.config import Config
from bot.client import app
from bot.handlers import register_handlers

async def start_bot_async():
    """Start bot with retry logic"""
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            await app.start()
            print("✅ Bot connected successfully!")
            await app.idle()
        except Exception as e:
            retry_count += 1
            if retry_count < max_retries:
                print(f"\n⚠️ Connection error: {str(e)[:50]}")
                print(f"Retrying ({retry_count}/{max_retries})...")
                await asyncio.sleep(5)
            else:
                print(f"\n❌ Failed after {max_retries} retries")
                raise

def main():
    print("=" * 50)
    print("AutoRenamer Bot - Ultra Simple Edition")
    print("=" * 50)
    
    if not Config.is_configured():
        print("\n❌ ERROR: Bot not configured!")
        sys.exit(1)
    
    print(f"\n✅ Configuration OK:")
    print(f"   API_ID: {Config.API_ID}")
    print(f"   Bot Token: Set")
    print(f"   Owner ID: {Config.OWNER_ID}\n")
    
    register_handlers(app)
    
    print("🚀 Starting bot...")
    print("📌 Send /start to begin\n")
    print("=" * 50)
    
    try:
        asyncio.run(start_bot_async())
    except KeyboardInterrupt:
        print("\n\n✅ Bot stopped by user")
    except Exception as e:
        print(f"\n❌ Bot error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
