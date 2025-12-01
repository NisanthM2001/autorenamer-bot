"""
AutoRenamer Bot - Main with Time Sync
Handles Telegram connectivity with proper error recovery
"""
import sys
import asyncio
import time
from pyrogram.errors import FloodWait, UnauthorizedError
from bot.config import Config
from bot.client import app
from bot.handlers import register_handlers

async def start_bot():
    """Start bot with robust error handling"""
    max_retries = 10
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            retry_count += 1
            print(f"\n🔄 Connecting to Telegram (attempt {retry_count}/{max_retries})...")
            
            # Connect to Telegram
            await app.start()
            print("✅ Bot connected successfully!")
            print("=" * 50)
            print("🚀 Bot is running and ready for commands")
            print("=" * 50)
            
            # Idle (wait for messages)
            await app.idle()
            return
            
        except FloodWait as e:
            wait_time = e.value
            print(f"\n⏳ Rate limited by Telegram: waiting {wait_time} seconds...")
            for remaining in range(min(wait_time, 60), 0, -1):
                print(f"   Waiting... {remaining} seconds left", end='\r')
                await asyncio.sleep(1)
            retry_count += 1
            
        except UnauthorizedError as e:
            print(f"\n❌ Authorization error: {e}")
            print("   Check your BOT_TOKEN in config")
            sys.exit(1)
            
        except Exception as e:
            error_str = str(e).lower()
            
            if "msg_id" in error_str or "time" in error_str:
                print(f"⏱️ Time sync issue - waiting before retry...")
                await asyncio.sleep(10)
                retry_count += 1
            elif "connection" in error_str or "network" in error_str:
                print(f"🌐 Connection issue: {str(e)[:60]}")
                await asyncio.sleep(5)
                retry_count += 1
            else:
                print(f"❌ Error: {e}")
                retry_count += 1
            
            if retry_count < max_retries:
                wait_time = min(5 * retry_count, 60)
                print(f"   Retrying in {wait_time} seconds...")
                await asyncio.sleep(wait_time)
    
    print(f"\n❌ Failed to connect after {max_retries} attempts")
    sys.exit(1)

def main():
    print("=" * 50)
    print("AutoRenamer Bot")
    print("=" * 50)
    
    if not Config.is_configured():
        print("\n❌ ERROR: Bot not configured!")
        print("Check credentials in bot/config.py")
        sys.exit(1)
    
    print(f"\n✅ Configuration loaded:")
    print(f"   API_ID: {Config.API_ID}")
    print(f"   Bot Token: ****** (set)")
    print(f"   Owner ID: {Config.OWNER_ID}\n")
    
    # Register command handlers
    register_handlers(app)
    
    print("Starting bot...")
    
    try:
        asyncio.run(start_bot())
    except KeyboardInterrupt:
        print("\n\n✅ Bot stopped by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
