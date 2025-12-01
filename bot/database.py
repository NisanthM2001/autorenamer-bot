"""
AutoRenamer Bot - No Database (Settings only in memory)
"""

# In-memory storage for this session only
SETTINGS = {
    "source_channels": [],
    "destination_channels": [],
    "whitelist_words": [],
    "blacklist_words": [],
    "removed_words": [],
    "file_prefix": "",
    "file_suffix": "",
    "remove_username": False,
    "custom_caption": "",
    "start_link": None,
    "end_link": None,
    "process_above_2gb": False,
}

def load_settings_sync():
    """Return in-memory settings"""
    return SETTINGS

async def save_settings(settings):
    """Save settings to memory"""
    global SETTINGS
    SETTINGS.update(settings)

async def get_setting(key, default=None):
    """Get a single setting"""
    return SETTINGS.get(key, default)

async def update_setting(key, value):
    """Update a single setting"""
    SETTINGS[key] = value
