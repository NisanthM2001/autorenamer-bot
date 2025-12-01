"""
MongoDB Database Module for AutoRenamer Bot
Replaces PostgreSQL with MongoDB for settings persistence
"""
import os
import json
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

# MongoDB Connection
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "autorenamer")
MONGODB_COLLECTION = os.getenv("MONGODB_COLLECTION", "settings")

client = None
db = None
settings_collection = None

def init_db():
    """Initialize MongoDB connection"""
    global client, db, settings_collection
    try:
        client = MongoClient(MONGODB_URL, serverSelectionTimeoutMS=5000)
        # Verify connection
        client.admin.command('ping')
        db = client[MONGODB_DB_NAME]
        settings_collection = db[MONGODB_COLLECTION]
        
        # Create index on _id for faster lookups
        settings_collection.create_index("_id")
        
        print("✅ MongoDB connected successfully")
        return True
    except ServerSelectionTimeoutError:
        print("⚠️ MongoDB connection timeout - using in-memory storage")
        return False
    except Exception as e:
        print(f"⚠️ MongoDB error: {e} - using in-memory storage")
        return False

# Initialize on startup
init_db()

# In-memory fallback for settings
in_memory_settings = {
    "_id": "bot_settings",
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
    "parallel_downloads": 1,
    "custom_thumbnail": None,
    "updated_at": datetime.now().isoformat()
}

def update_setting(key, value):
    """Update a single setting"""
    try:
        if settings_collection:
            settings_collection.update_one(
                {"_id": "bot_settings"},
                {"$set": {key: value, "updated_at": datetime.now().isoformat()}},
                upsert=True
            )
            print(f"✅ Setting updated: {key}")
            return True
    except Exception as e:
        print(f"⚠️ Error updating setting: {e}")
    
    # Fallback to in-memory
    in_memory_settings[key] = value
    return True

def save_settings(settings_dict):
    """Save all settings at once"""
    try:
        if settings_collection:
            settings_dict["_id"] = "bot_settings"
            settings_dict["updated_at"] = datetime.now().isoformat()
            settings_collection.replace_one(
                {"_id": "bot_settings"},
                settings_dict,
                upsert=True
            )
            print(f"✅ Settings saved to MongoDB")
            return True
    except Exception as e:
        print(f"⚠️ Error saving settings: {e}")
    
    # Fallback to in-memory
    in_memory_settings.update(settings_dict)
    return True

def load_settings_sync():
    """Load all settings (synchronous)"""
    try:
        if settings_collection:
            doc = settings_collection.find_one({"_id": "bot_settings"})
            if doc:
                # Remove MongoDB _id field before returning
                doc.pop("_id", None)
                return doc
    except Exception as e:
        print(f"⚠️ Error loading settings: {e}")
    
    # Return in-memory settings
    return {k: v for k, v in in_memory_settings.items() if k != "_id"}

def save_backup():
    """Save backup of all settings"""
    try:
        settings = load_settings_sync()
        backup_path = "settings_backup.json"
        with open(backup_path, 'w') as f:
            json.dump(settings, f, indent=4, default=str)
        print(f"✅ Settings backed up to {backup_path}")
        return True
    except Exception as e:
        print(f"❌ Error creating backup: {e}")
        return False

def load_backup():
    """Restore settings from backup"""
    try:
        backup_path = "settings_backup.json"
        with open(backup_path, 'r') as f:
            settings = json.load(f)
        save_settings(settings)
        print(f"✅ Settings restored from backup")
        return True
    except Exception as e:
        print(f"❌ Error restoring backup: {e}")
        return False

def delete_all_settings():
    """Clear all settings"""
    try:
        if settings_collection:
            settings_collection.delete_many({})
        in_memory_settings.clear()
        in_memory_settings["_id"] = "bot_settings"
        print("✅ All settings cleared")
        return True
    except Exception as e:
        print(f"❌ Error clearing settings: {e}")
        return False

