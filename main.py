"""
AutoRenamer Bot - Robust Main with FLOOD_WAIT handling
"""
import sys
import asyncio
import time
from pyrogram.errors import FloodWait
from bot.config import Config
from bot.client import app
from bot.handlers import register_handlers

async def start_bot_with_exponential_backoff():
    """Start bot with exponential backoff and FLOOD_WAIT handling"""
    max_retries = 5
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            print(f"\n🔄 Connecting to Telegram (attempt {retry_count + 1}/{max_retries})...")
            await app.start()
            print("✅ Bot connected to Telegram successfully!")
            await app.idle()
            return
        except FloodWait as e:
            wait_time = e.value
            print(f"\n⚠️ FLOOD_WAIT: Telegram is rate-limiting. Waiting {wait_time} seconds...")
            print(f"   Please be patient - this is normal when bot restarts frequently")
            for i in range(min(wait_time, 60)):  # Cap display at 60 seconds
                print(f"   Waiting... {i+1}/{min(wait_time, 60)}", end='\r')
                await asyncio.sleep(1)
            retry_count += 1
        except Exception as e:
            error_msg = str(e)
            if "msg_id" in error_msg.lower():
                print(f"\n⚠️ Time sync error: {error_msg}")
                print("   Waiting 30 seconds before retry...")
                await asyncio.sleep(30)
            else:
                print(f"\n⚠️ Connection error: {error_msg[:80]}")
                
            retry_count += 1
            if retry_count < max_retries:
                wait = min(10 * (2 ** retry_count), 300)  # Exponential backoff, max 5min
                print(f"   Retrying in {wait} seconds...")
                await asyncio.sleep(wait)
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
        asyncio.run(start_bot_with_exponential_backoff())
    except KeyboardInterrupt:
        print("\n\n✅ Bot stopped by user")
    except Exception as e:
        print(f"\n❌ Bot error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
