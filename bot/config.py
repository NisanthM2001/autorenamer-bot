"""
AutoRenamer Bot - Simple Config (No Database)
Just download and upload - no persistent storage
"""
import os

class Config:
    # ============ TELEGRAM API CREDENTIALS ============
    API_ID = 25713073
    API_HASH = "65a23aaa7a97f42475de52ed240af2f3"
    BOT_TOKEN = "8155671926:AAFm2V87F76qj_gEm_gJFD-mknWHHzqGxzo"
    OWNER_ID = 6927710017
    
    # ============ BOT SETTINGS ============
    DOWNLOAD_DIR = "downloads"
    THUMBNAIL_DIR = "thumbnails"
    
    # ============ DEFAULT FILE PROCESSING ============
    FILE_PREFIX = ""
    FILE_SUFFIX = ""
    REMOVE_USERNAME = True
    REMOVE_WWW_PATTERNS = True
    CUSTOM_CAPTION = "{filename}\n📊 Size: {filesize}"
    
    # ============ FILTERING OPTIONS ============
    WHITELIST_WORDS = []
    BLACKLIST_WORDS = []
    REMOVED_WORDS = []
    
    # ============ PROCESSING OPTIONS ============
    PROCESS_ABOVE_2GB = False
    
    # ============ CHANNEL SETTINGS (SET VIA COMMANDS) ============
    SOURCE_CHANNEL_IDS = []
    DESTINATION_CHANNEL_IDS = []
    START_LINK = None
    END_LINK = None
    
    @classmethod
    def is_configured(cls):
        """Check if credentials are set"""
        return all([cls.API_ID, cls.API_HASH, cls.BOT_TOKEN, cls.OWNER_ID])
    
    @classmethod
    def get_info(cls):
        return {
            "api_configured": bool(cls.API_ID and cls.API_HASH),
            "bot_token_set": bool(cls.BOT_TOKEN),
            "owner_id_set": bool(cls.OWNER_ID),
        }
