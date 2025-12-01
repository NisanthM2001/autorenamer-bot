"""
AutoRenamer Bot Configuration - Hardcoded Credentials
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # ============ TELEGRAM API CREDENTIALS ============
    API_ID = 25713073
    API_HASH = "65a23aaa7a97f42475de52ed240af2f3"
    BOT_TOKEN = "8155671926:AAFm2V87F76qj_gEm_gJFD-mknWHHzqGxzo"
    OWNER_ID = 6927710017
    SESSION_STRING = os.getenv("SESSION_STRING", "")
    LOG_CHANNEL_ID = os.getenv("LOG_CHANNEL_ID", "")
    
    # ============ MONGODB CONFIGURATION ============
    MONGODB_URL = "mongodb+srv://leechbot:leechbot01@cluster0.vxfsb.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    MONGODB_DB_NAME = "autorenamer"
    MONGODB_COLLECTION = "settings"
    
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
    SOURCE_CHANNEL_IDS = []
    DESTINATION_CHANNEL_IDS = []
    
    # ============ MESSAGE RANGE ============
    START_LINK = None
    END_LINK = None
    
    @classmethod
    def is_configured(cls):
        """Check if all credentials are properly configured"""
        return all([
            cls.API_ID != 0,
            cls.API_HASH and cls.API_HASH.strip() != "",
            cls.BOT_TOKEN and cls.BOT_TOKEN.strip() != "",
            cls.OWNER_ID != 0,
        ])
    
    @classmethod
    def get_info(cls):
        """Get configuration information"""
        return {
            "api_configured": bool(cls.API_ID != 0 and cls.API_HASH),
            "bot_token_set": bool(cls.BOT_TOKEN),
            "owner_id_set": bool(cls.OWNER_ID != 0),
            "mongodb_configured": bool(cls.MONGODB_URL),
            "source_channels": len(cls.SOURCE_CHANNEL_IDS),
            "destination_channels": len(cls.DESTINATION_CHANNEL_IDS),
            "whitelist_words": cls.WHITELIST_WORDS,
            "blacklist_words": cls.BLACKLIST_WORDS,
        }
