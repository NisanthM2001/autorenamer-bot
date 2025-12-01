"""
MongoDB Configuration for AutoRenamer Bot
All settings in one config file - no .env needed
"""

class Config:
    # ============ TELEGRAM API CREDENTIALS ============
    API_ID = "25713073"   # Get from https://my.telegram.org
    API_HASH = "65a23aaa7a97f42475de52ed240af2f3" 
    BOT_TOKEN = "8155671926:AAFm2V87F76qj_gEm_gJFD-mknWHHzqGxzo"
    OWNER_ID = "6927710017"  # Your Telegram user ID
    SESSION_STRING = ""  # Optional: Pyrogram session string
    LOG_CHANNEL_ID = ""  # Optional: Channel ID for logging
    
    # ============ MONGODB CONFIGURATION ============
    MONGODB_URL = "mongodb+srv://leechbot:leechbot01@cluster0.vxfsb.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    MONGODB_DB_NAME = "autorenamer"
    MONGODB_COLLECTION = "settings"
    
    # ============ BOT SETTINGS ============
    DOWNLOAD_DIR = "downloads"
    THUMBNAIL_DIR = "thumbnails"
    
    # ============ DEFAULT FILE PROCESSING ============
    FILE_PREFIX = ""  # Prefix to add to renamed files
    FILE_SUFFIX = ""  # Suffix to add to renamed files
    REMOVE_USERNAME = True  # Remove @username from filenames
    REMOVE_WWW_PATTERNS = True  # Remove www.site.* patterns
    CUSTOM_CAPTION = "{filename}\n📊 Size: {filesize}\n🌐 Language: {language}"
    
    # ============ FILTERING OPTIONS ============
    WHITELIST_WORDS = []  # Empty = allow all | Filled = only these keywords
    BLACKLIST_WORDS = []  # Don't process files with these keywords
    REMOVED_WORDS = []  # Case-sensitive words to remove from filenames
    
    # ============ PROCESSING OPTIONS ============
    PROCESS_ABOVE_2GB = False  # Requires Telegram Premium account
    MAX_PARALLEL_DOWNLOADS = 1  # Download one file at a time
    
    # ============ LANGUAGE & SUBTITLE DETECTION ============
    AUTO_DETECT_LANGUAGE = True
    SUPPORTED_LANGUAGES = ["English", "Hindi", "Telugu", "Kannada", "Tamil", "Malayalam", "Punjabi"]
    SUPPORTED_SUBTITLES = ["English", "Hindi", "Telugu", "Kannada", "Tamil", "Malayalam", "Punjabi"]
    
    # ============ CHANNEL SETTINGS ============
    SOURCE_CHANNELS = []  # Source channel IDs to download from
    DESTINATION_CHANNELS = []  # Destination channel IDs to upload to
    
    # ============ MESSAGE RANGE ============
    START_MESSAGE_LINK = None  # Starting message link
    END_MESSAGE_LINK = None  # Ending message link
    
    @classmethod
    def is_configured(cls):
        """Check if essential configurations are set"""
        return all([
            cls.API_ID != "25713073",
            cls.API_HASH != "65a23aaa7a97f42475de52ed240af2f3",
            cls.BOT_TOKEN != "8155671926:AAFm2V87F76qj_gEm_gJFD-mknWHHzqGxzo",
            cls.OWNER_ID != 6927710017,
            "mongodb" in cls.MONGODB_URL,
        ])
    
    @classmethod
    def get_info(cls):
        """Get configuration information"""
        return {
            "api_id": cls.API_ID,
            "bot_token_configured": bool(cls.BOT_TOKEN != "8155671926:AAFm2V87F76qj_gEm_gJFD-mknWHHzqGxzo"),
            "mongodb_configured": bool("mongodb" in cls.MONGODB_URL),
            "source_channels": len(cls.SOURCE_CHANNELS),
            "destination_channels": len(cls.DESTINATION_CHANNELS),
            "whitelist_words": cls.WHITELIST_WORDS,
            "blacklist_words": cls.BLACKLIST_WORDS,
            "file_prefix": cls.FILE_PREFIX,
            "file_suffix": cls.FILE_SUFFIX,
        }
