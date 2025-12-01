"""
Database - Not used in ultra simple version
Kept for compatibility only
"""

def load_settings_sync():
    return {}

async def save_settings(settings):
    pass

async def get_setting(key, default=None):
    return default

async def update_setting(key, value):
    pass
