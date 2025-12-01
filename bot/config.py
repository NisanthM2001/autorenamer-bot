"""
AutoRenamer Bot Configuration
"""

class Config:
    # ============ TELEGRAM API CREDENTIALS ============
    API_ID = 25713073
    API_HASH = "65a23aaa7a97f42475de52ed240af2f3"
    BOT_TOKEN = "8155671926:AAFm2V87F76qj_gEm_gJFD-mknWHHzqGxzo"
    OWNER_ID = 6927710017
    
    # ============ BOT SETTINGS ============
    DOWNLOAD_DIR = "downloads"
    THUMBNAIL_DIR = "thumbnails"
    
    # ============ CHANNEL SETTINGS ============
    SOURCE_CHANNEL_IDS = []
    DESTINATION_CHANNEL_IDS = []
    
    @classmethod
    def is_configured(cls):
        return all([cls.API_ID, cls.API_HASH, cls.BOT_TOKEN, cls.OWNER_ID])
