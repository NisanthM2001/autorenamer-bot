"""
AutoRenamer Bot - Main Entry Point
Ultra Simple - No Database, No Sessions
"""
import sys
from bot.config import Config
from bot.client import app
from bot.handlers import register_handlers

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
    
    app.run()

if __name__ == "__main__":
    main()
