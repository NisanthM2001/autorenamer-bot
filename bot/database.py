import os
import asyncio
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

# PostgreSQL connection
DATABASE_URL = os.getenv("DATABASE_URL", "")

def get_db_connection():
    """Get PostgreSQL connection"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        print(f"❌ PostgreSQL connection error: {e}")
        return None

def init_db():
    """Initialize database tables"""
    conn = get_db_connection()
    if not conn:
        print("⚠️ Cannot initialize database - no connection")
        return False
    
    try:
        cursor = conn.cursor()
        
        # Create settings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                _id VARCHAR(50) PRIMARY KEY,
                source_channels TEXT,
                destination_channels TEXT,
                whitelist_words TEXT,
                blacklist_words TEXT,
                removed_words TEXT,
                file_prefix VARCHAR(255),
                file_suffix VARCHAR(255),
                remove_username BOOLEAN,
                custom_caption TEXT,
                start_link VARCHAR(255),
                end_link VARCHAR(255),
                process_above_2gb BOOLEAN,
                parallel_downloads INTEGER,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        print("✅ Database tables initialized")
        return True
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

# Initialize on startup
init_db()

# In-memory fallback for settings
in_memory_settings = {
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
    "parallel_downloads": 1
}

def load_settings_sync():
    """Synchronously load settings from PostgreSQL or memory at startup"""
    global in_memory_settings
    
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("SELECT * FROM settings WHERE _id = %s", ("main_settings",))
            row = cursor.fetchone()
            
            if row:
                import json
                in_memory_settings = {
                    "source_channels": json.loads(row.get("source_channels") or "[]"),
                    "destination_channels": json.loads(row.get("destination_channels") or "[]"),
                    "whitelist_words": json.loads(row.get("whitelist_words") or "[]"),
                    "blacklist_words": json.loads(row.get("blacklist_words") or "[]"),
                    "removed_words": json.loads(row.get("removed_words") or "[]"),
                    "file_prefix": row.get("file_prefix") or "",
                    "file_suffix": row.get("file_suffix") or "",
                    "remove_username": row.get("remove_username") or False,
                    "custom_caption": row.get("custom_caption") or "",
                    "start_link": row.get("start_link"),
                    "end_link": row.get("end_link"),
                    "process_above_2gb": row.get("process_above_2gb") or False,
                    "parallel_downloads": row.get("parallel_downloads") or 1
                }
                print(f"✅ Settings loaded from PostgreSQL")
                return in_memory_settings
        except Exception as e:
            print(f"❌ Error loading from PostgreSQL: {e}")
        finally:
            cursor.close()
            conn.close()
    
    print(f"✅ Using in-memory settings")
    return in_memory_settings

async def load_settings():
    """Load all settings from PostgreSQL or memory"""
    global in_memory_settings
    
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("SELECT * FROM settings WHERE _id = %s", ("main_settings",))
            row = cursor.fetchone()
            
            if row:
                import json
                return {
                    "source_channels": json.loads(row.get("source_channels") or "[]"),
                    "destination_channels": json.loads(row.get("destination_channels") or "[]"),
                    "whitelist_words": json.loads(row.get("whitelist_words") or "[]"),
                    "blacklist_words": json.loads(row.get("blacklist_words") or "[]"),
                    "removed_words": json.loads(row.get("removed_words") or "[]"),
                    "file_prefix": row.get("file_prefix") or "",
                    "file_suffix": row.get("file_suffix") or "",
                    "remove_username": row.get("remove_username") or False,
                    "custom_caption": row.get("custom_caption") or "",
                    "start_link": row.get("start_link"),
                    "end_link": row.get("end_link"),
                    "process_above_2gb": row.get("process_above_2gb") or False,
                    "parallel_downloads": row.get("parallel_downloads") or 1
                }
        except Exception as e:
            print(f"❌ Error loading settings from PostgreSQL: {e}")
        finally:
            cursor.close()
            conn.close()
    
    return in_memory_settings

async def save_settings(settings_dict):
    """Save settings to PostgreSQL or memory"""
    global in_memory_settings
    import json
    
    in_memory_settings = settings_dict
    
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO settings 
                (_id, source_channels, destination_channels, whitelist_words, blacklist_words, removed_words,
                 file_prefix, file_suffix, remove_username, custom_caption, start_link, end_link,
                 process_above_2gb, parallel_downloads, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (_id) DO UPDATE SET
                    source_channels = EXCLUDED.source_channels,
                    destination_channels = EXCLUDED.destination_channels,
                    whitelist_words = EXCLUDED.whitelist_words,
                    blacklist_words = EXCLUDED.blacklist_words,
                    removed_words = EXCLUDED.removed_words,
                    file_prefix = EXCLUDED.file_prefix,
                    file_suffix = EXCLUDED.file_suffix,
                    remove_username = EXCLUDED.remove_username,
                    custom_caption = EXCLUDED.custom_caption,
                    start_link = EXCLUDED.start_link,
                    end_link = EXCLUDED.end_link,
                    process_above_2gb = EXCLUDED.process_above_2gb,
                    parallel_downloads = EXCLUDED.parallel_downloads,
                    updated_at = CURRENT_TIMESTAMP
            """, (
                "main_settings",
                json.dumps(settings_dict.get("source_channels", [])),
                json.dumps(settings_dict.get("destination_channels", [])),
                json.dumps(settings_dict.get("whitelist_words", [])),
                json.dumps(settings_dict.get("blacklist_words", [])),
                json.dumps(settings_dict.get("removed_words", [])),
                settings_dict.get("file_prefix", ""),
                settings_dict.get("file_suffix", ""),
                settings_dict.get("remove_username", False),
                settings_dict.get("custom_caption", ""),
                settings_dict.get("start_link"),
                settings_dict.get("end_link"),
                settings_dict.get("process_above_2gb", False),
                settings_dict.get("parallel_downloads", 1),
                datetime.utcnow()
            ))
            
            conn.commit()
        except Exception as e:
            print(f"❌ Error saving settings to PostgreSQL: {e}")
        finally:
            cursor.close()
            conn.close()

async def update_setting(key, value):
    """Update a single setting"""
    global in_memory_settings
    import json
    
    in_memory_settings[key] = value
    
    # Load current settings and update
    current = await load_settings()
    current[key] = value
    await save_settings(current)

async def delete_setting(key):
    """Delete a specific setting (reset to default)"""
    global in_memory_settings
    
    defaults = {
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
        "parallel_downloads": 1
    }
    
    if key in defaults:
        in_memory_settings[key] = defaults[key]
        current = await load_settings()
        current[key] = defaults[key]
        await save_settings(current)

async def save_backup(settings_dict):
    """Save settings to backup in PostgreSQL (replaces old backup)"""
    import json
    
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO settings 
                (_id, source_channels, destination_channels, whitelist_words, blacklist_words, removed_words,
                 file_prefix, file_suffix, remove_username, custom_caption, start_link, end_link,
                 process_above_2gb, parallel_downloads, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (_id) DO UPDATE SET
                    source_channels = EXCLUDED.source_channels,
                    destination_channels = EXCLUDED.destination_channels,
                    whitelist_words = EXCLUDED.whitelist_words,
                    blacklist_words = EXCLUDED.blacklist_words,
                    removed_words = EXCLUDED.removed_words,
                    file_prefix = EXCLUDED.file_prefix,
                    file_suffix = EXCLUDED.file_suffix,
                    remove_username = EXCLUDED.remove_username,
                    custom_caption = EXCLUDED.custom_caption,
                    start_link = EXCLUDED.start_link,
                    end_link = EXCLUDED.end_link,
                    process_above_2gb = EXCLUDED.process_above_2gb,
                    parallel_downloads = EXCLUDED.parallel_downloads,
                    updated_at = CURRENT_TIMESTAMP
            """, (
                "backup_settings",
                json.dumps(settings_dict.get("source_channels", [])),
                json.dumps(settings_dict.get("destination_channels", [])),
                json.dumps(settings_dict.get("whitelist_words", [])),
                json.dumps(settings_dict.get("blacklist_words", [])),
                json.dumps(settings_dict.get("removed_words", [])),
                settings_dict.get("file_prefix", ""),
                settings_dict.get("file_suffix", ""),
                settings_dict.get("remove_username", False),
                settings_dict.get("custom_caption", ""),
                settings_dict.get("start_link"),
                settings_dict.get("end_link"),
                settings_dict.get("process_above_2gb", False),
                settings_dict.get("parallel_downloads", 1),
                datetime.utcnow()
            ))
            
            conn.commit()
            print("✅ Backup saved successfully to PostgreSQL")
            return True
        except Exception as e:
            print(f"❌ Error saving backup: {e}")
            return False
        finally:
            cursor.close()
            conn.close()
    return False

async def load_backup():
    """Load settings from PostgreSQL backup"""
    import json
    
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("SELECT * FROM settings WHERE _id = %s", ("backup_settings",))
            row = cursor.fetchone()
            
            if row:
                return {
                    "source_channels": json.loads(row.get("source_channels") or "[]"),
                    "destination_channels": json.loads(row.get("destination_channels") or "[]"),
                    "whitelist_words": json.loads(row.get("whitelist_words") or "[]"),
                    "blacklist_words": json.loads(row.get("blacklist_words") or "[]"),
                    "removed_words": json.loads(row.get("removed_words") or "[]"),
                    "file_prefix": row.get("file_prefix") or "",
                    "file_suffix": row.get("file_suffix") or "",
                    "remove_username": row.get("remove_username") or False,
                    "custom_caption": row.get("custom_caption") or "",
                    "start_link": row.get("start_link"),
                    "end_link": row.get("end_link"),
                    "process_above_2gb": row.get("process_above_2gb") or False,
                    "parallel_downloads": row.get("parallel_downloads") or 1
                }
        except Exception as e:
            print(f"❌ Error loading backup: {e}")
        finally:
            cursor.close()
            conn.close()
    return None
