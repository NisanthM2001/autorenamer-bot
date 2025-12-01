"""
Configuration for AutoRenamer Bot
Reads all credentials from environment variables
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # ============ TELEGRAM API CREDENTIALS (from env vars) ============
    API_ID = int(os.getenv("API_ID", "0"))
    API_HASH = os.getenv("API_HASH", "")
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    OWNER_ID = int(os.getenv("OWNER_ID", "0"))
    SESSION_STRING = os.getenv("SESSION_STRING", "")
    LOG_CHANNEL_ID = os.getenv("LOG_CHANNEL_ID", "")
    
    # ============ MONGODB CONFIGURATION (from env vars) ============
    MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "autorenamer")
    MONGODB_COLLECTION = os.getenv("MONGODB_COLLECTION", "settings")
    
    # ============ BOT SETTINGS ============
    DOWNLOAD_DIR = "downloads"
    THUMBNAIL_DIR = "thumbnails"
    
    # ============ DEFAULT FILE PROCESSING ============
    FILE_PREFIX = ""
    FILE_SUFFIX = ""
    REMOVE_USERNAME = True
    REMOVE_WWW_PATTERNS = True
    CUSTOM_CAPTION = "{filename}\n📊 Size: {filesize}\n🌐 Language: {language}"
    
    # ============ FILTERING OPTIONS ============
    WHITELIST_WORDS = []
    BLACKLIST_WORDS = []
    REMOVED_WORDS = []
    
    # ============ PROCESSING OPTIONS ============
    PROCESS_ABOVE_2GB = False
    MAX_PARALLEL_DOWNLOADS = 1
    
    # ============ LANGUAGE & SUBTITLE DETECTION ============
    AUTO_DETECT_LANGUAGE = True
    SUPPORTED_LANGUAGES = ["English", "Hindi", "Telugu", "Kannada", "Tamil", "Malayalam", "Punjabi"]
    SUPPORTED_SUBTITLES = ["English", "Hindi", "Telugu", "Kannada", "Tamil", "Malayalam", "Punjabi"]
    
    # ============ CHANNEL SETTINGS ============
    SOURCE_CHANNELS = []
    DESTINATION_CHANNELS = []
    
    # ============ MESSAGE RANGE ============
    START_MESSAGE_LINK = None
    END_MESSAGE_LINK = None
    
    @classmethod
    def is_configured(cls):
        """Check if essential configurations are set"""
        return all([
            cls.API_ID and cls.API_ID != 0,
            cls.API_HASH and cls.API_HASH != "",
            cls.BOT_TOKEN and cls.BOT_TOKEN != "",
            cls.OWNER_ID and cls.OWNER_ID != 0,
        ])
    
    @classmethod
    def get_info(cls):
        """Get configuration information"""
        return {
            "api_configured": bool(cls.API_ID and cls.API_HASH),
            "bot_token_set": bool(cls.BOT_TOKEN),
            "owner_id_set": bool(cls.OWNER_ID),
            "mongodb_configured": bool(cls.MONGODB_URL and "mongodb" in cls.MONGODB_URL),
            "source_channels": len(cls.SOURCE_CHANNELS),
            "destination_channels": len(cls.DESTINATION_CHANNELS),
        }
