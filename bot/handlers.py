import os
import re
import sys
import asyncio
import json
from pyrogram.client import Client
from pyrogram import filters
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from bot.config import Config
from bot.thumbnail import save_thumbnail, delete_thumbnail, has_thumbnail, get_thumbnail
from bot.processor import process_range, get_status_text, current_status
from bot.database import update_setting, save_settings, save_backup, load_backup

user_data: dict[int, dict] = {}

def is_owner(_, __, message: Message):
    return message.from_user and message.from_user.id == Config.OWNER_ID

def is_owner_callback(_, __, callback: CallbackQuery):
    return callback.from_user and callback.from_user.id == Config.OWNER_ID

owner_filter = filters.create(is_owner)
owner_callback_filter = filters.create(is_owner_callback)

def get_main_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Settings", callback_data="menu_settings"),
            InlineKeyboardButton("Set Range", callback_data="menu_setrange")
        ],
        [
            InlineKeyboardButton("Process", callback_data="menu_process"),
            InlineKeyboardButton("Help", callback_data="menu_help")
        ]
    ])

def get_settings_menu():
    remove_username_status = "✅ ON" if Config.REMOVE_USERNAME else "❌ OFF"
    premium_status = "✅ ON" if Config.PROCESS_ABOVE_2GB else "❌ OFF"
    thumb_exists = has_thumbnail()
    
    buttons = [
        [
            InlineKeyboardButton("Source Channels", callback_data="set_source"),
            InlineKeyboardButton("Dest Channels", callback_data="set_dest")
        ],
        [
            InlineKeyboardButton("Whitelist", callback_data="set_whitelist"),
            InlineKeyboardButton("Blacklist", callback_data="set_blacklist")
        ],
        [
            InlineKeyboardButton("Remove Words", callback_data="set_removed_words")
        ],
        [
            InlineKeyboardButton("Prefix", callback_data="set_prefix"),
            InlineKeyboardButton("Suffix", callback_data="set_suffix")
        ],
        [
            InlineKeyboardButton(f"Remove Username {remove_username_status}", callback_data="toggle_remove_username"),
            InlineKeyboardButton("Set Caption", callback_data="set_caption")
        ],
        [
            InlineKeyboardButton(f"Premium (>2GB) {premium_status}", callback_data="toggle_premium")
        ]
    ]
    
    # Dynamic thumbnail buttons
    if thumb_exists:
        buttons.append([
            InlineKeyboardButton("📸 Send Thumbnail", callback_data="send_thumb"),
            InlineKeyboardButton("🗑️ Delete Thumbnail", callback_data="del_thumb")
        ])
    else:
        buttons.append([
            InlineKeyboardButton("📸 Set Thumbnail", callback_data="set_thumb")
        ])
    
    buttons.extend([
        [
            InlineKeyboardButton("📤 Backup Settings", callback_data="export_settings"),
            InlineKeyboardButton("♻️ Restore Settings", callback_data="restore_settings")
        ],
        [
            InlineKeyboardButton("🔴 Reset All", callback_data="reset_all"),
            InlineKeyboardButton("Back to Menu", callback_data="menu_main")
        ]
    ])
    
    return InlineKeyboardMarkup(buttons)

def get_cancel_button():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Cancel", callback_data="cancel_input")]
    ])

def get_process_control_buttons():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🛑 Cancel All", callback_data="cancel_all_now")
        ]
    ])

def get_back_button(callback_data="menu_main"):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Back to Menu", callback_data=callback_data)]
    ])

def format_channel_list(channels):
    if not channels:
        return "None"
    return ", ".join(str(c) for c in channels)

def parse_channel_ids(text: str) -> tuple[list, str]:
    channels = []
    errors = []
    
    for part in text.split(","):
        part = part.strip()
        if not part:
            continue
        
        if part.startswith('@'):
            if re.match(r'^@[a-zA-Z][a-zA-Z0-9_]{3,}$', part):
                channels.append(part)
            else:
                errors.append(f"Invalid username: {part}")
        elif part.lstrip('-').isdigit():
            num = int(part)
            str_num = str(abs(num))
            if num < 0 and str_num.startswith('100') and len(str_num) >= 13:
                channels.append(num)
            else:
                errors.append(f"Invalid channel ID: {part} (must be like -100XXXXXXXXXX)")
        else:
            errors.append(f"Invalid format: {part}")
    
    if errors:
        return [], ", ".join(errors)
    
    return channels, ""

def get_main_menu_text():
    info = Config.get_info()
    return f"""
**Channel File Processor Bot**

**Current Configuration:**
- Source Channels: {info['source_channels']}
- Destination Channels: {info['destination_channels']}
- Thumbnail: {'Set' if has_thumbnail() else 'Not set'}
- Whitelist: {', '.join(info['whitelist_words']) if info['whitelist_words'] else 'None'}
- Blacklist: {', '.join(info['blacklist_words']) if info['blacklist_words'] else 'None'}

Use the buttons below to configure and control the bot.
    """

def get_settings_text():
    return f"""
🎯 **ALL SETTINGS**

📥 **Source Channels:**
{format_channel_list(Config.SOURCE_CHANNEL_IDS) if Config.SOURCE_CHANNEL_IDS else '❌ Not set'}

📤 **Destination Channels:**
{format_channel_list(Config.DESTINATION_CHANNEL_IDS) if Config.DESTINATION_CHANNEL_IDS else '❌ Not set'}

🏷️ **File Naming:**
• Prefix: {Config.FILE_PREFIX or '❌ None'}
• Suffix: {Config.FILE_SUFFIX or '❌ None'}

✂️ **Remove Words:** {', '.join(Config.REMOVED_WORDS) if Config.REMOVED_WORDS else '❌ None'}

🚫 **Filters:**
• Whitelist: {', '.join(Config.WHITELIST_WORDS) if Config.WHITELIST_WORDS else '❌ None'}
• Blacklist: {', '.join(Config.BLACKLIST_WORDS) if Config.BLACKLIST_WORDS else '❌ None'}

👤 **Username Removal:** {'✅ ON' if Config.REMOVE_USERNAME else '❌ OFF'}

💬 **Custom Caption:** {Config.CUSTOM_CAPTION or '❌ None'}

📸 **Thumbnail:** {'✅ Set' if has_thumbnail() else '❌ Not set'}

📋 **Message Range:**
• Start: {Config.START_LINK or '❌ Not set'}
• End: {Config.END_LINK or '❌ Not set'}

⭐ **Premium Mode:** {'✅ ON' if Config.PROCESS_ABOVE_2GB else '❌ OFF'}

Click a button below to edit.
    """

def register_handlers(app: Client):
    
    @app.on_message(filters.command("start") & filters.private)
    async def start_command(client: Client, message: Message):
        user_id = message.from_user.id
        if user_id in user_data:
            user_data[user_id]['waiting_for'] = None
            user_data[user_id]['menu_message'] = None
        
        if not Config.is_configured():
            await message.reply_text(
                "Bot is not configured!\n\n"
                "Please set the following environment variables:\n"
                "- API_ID\n"
                "- API_HASH\n"
                "- BOT_TOKEN\n"
                "- OWNER_ID"
            )
            return
        
        # Check if bot just restarted
        restart_flag = "/tmp/bot_restart_flag"
        restart_msg = ""
        if os.path.exists(restart_flag):
            restart_msg = "✅ **Successfully restarted!**\n\n"
            try:
                os.remove(restart_flag)
            except:
                pass
        
        menu_msg = await message.reply_text(restart_msg + get_main_menu_text(), reply_markup=get_main_menu())
        
        if user_id not in user_data:
            user_data[user_id] = {}
        user_data[user_id]['menu_message'] = menu_msg
    
    @app.on_callback_query(filters.regex("^cancel_input$") & owner_callback_filter)
    async def cancel_input_callback(client: Client, callback: CallbackQuery):
        user_id = callback.from_user.id
        if user_id in user_data:
            user_data[user_id]['waiting_for'] = None
        
        await callback.message.edit_text(get_main_menu_text(), reply_markup=get_main_menu())
        await callback.answer("Cancelled")
    
    @app.on_callback_query(filters.regex("^menu_main$") & owner_callback_filter)
    async def main_menu_callback(client: Client, callback: CallbackQuery):
        user_id = callback.from_user.id
        if user_id in user_data:
            user_data[user_id]['waiting_for'] = None
            user_data[user_id]['menu_message'] = callback.message
        
        await callback.message.edit_text(get_main_menu_text(), reply_markup=get_main_menu())
        await callback.answer()
    
    @app.on_callback_query(filters.regex("^menu_settings$") & owner_callback_filter)
    async def settings_menu_callback(client: Client, callback: CallbackQuery):
        user_id = callback.from_user.id
        if user_id in user_data:
            user_data[user_id]['waiting_for'] = None
            user_data[user_id]['menu_message'] = callback.message
        else:
            user_data[user_id] = {'menu_message': callback.message}
        
        await callback.message.edit_text(get_settings_text(), reply_markup=get_settings_menu())
        await callback.answer()
    
    @app.on_callback_query(filters.regex("^menu_status$") & owner_callback_filter)
    async def status_callback(client: Client, callback: CallbackQuery):
        user_id = callback.from_user.id
        data = user_data.get(user_id, {})
        
        status_text = f"""
**Current Status**

**Range:**
- Start: {data.get('start_link', 'Not set')}
- End: {data.get('end_link', 'Not set')}

**Channels:**
- Source: {format_channel_list(Config.SOURCE_CHANNEL_IDS)}
- Destination: {format_channel_list(Config.DESTINATION_CHANNEL_IDS)}

**Filters:**
- Whitelist: {', '.join(Config.WHITELIST_WORDS) if Config.WHITELIST_WORDS else 'None'}
- Blacklist: {', '.join(Config.BLACKLIST_WORDS) if Config.BLACKLIST_WORDS else 'None'}

**File Naming:**
- Prefix: {Config.FILE_PREFIX or 'None'}
- Suffix: {Config.FILE_SUFFIX or 'None'}

**Thumbnail:** {'Set' if has_thumbnail() else 'Not set'}
        """
        await callback.message.edit_text(status_text, reply_markup=get_back_button())
        await callback.answer()
    
    @app.on_callback_query(filters.regex("^menu_help$") & owner_callback_filter)
    async def help_callback(client: Client, callback: CallbackQuery):
        help_text = f"""
**📋 COMPLETE SETUP GUIDE**

**🎯 CHANNEL SETUP**
👉 Source Channels (📥)
   - Where to download files FROM
   - Enter channel IDs like: -1001234567890
   - Multiple channels: -1001234567890, -1009876543210
   - Current: {format_channel_list(Config.SOURCE_CHANNEL_IDS) if Config.SOURCE_CHANNEL_IDS else 'None'}

👉 Destination Channels (📤)
   - Where to upload files TO
   - Enter channel IDs in same format as source
   - Multiple channels: send all files to each destination
   - Current: {format_channel_list(Config.DESTINATION_CHANNEL_IDS) if Config.DESTINATION_CHANNEL_IDS else 'None'}

**📨 MESSAGE RANGE**
- Start Link & End Link from Telegram
- Bot will process all messages between these links
- Must be from SAME channel
- Format: https://t.me/c/123456789/1 https://t.me/c/123456789/100
- Current Range: {f"{Config.START_LINK} to {Config.END_LINK}" if Config.START_LINK and Config.END_LINK else "Not set"}

**🔍 FILTERS**
👉 Whitelist (Allow specific files)
   - Only process files with THESE words
   - Example: "movie,episode,series"
   - Current: {', '.join(Config.WHITELIST_WORDS) if Config.WHITELIST_WORDS else 'None (process all)'}

👉 Blacklist (Block specific files)
   - SKIP files with THESE words
   - Example: "sample,trailer,teaser"
   - Current: {', '.join(Config.BLACKLIST_WORDS) if Config.BLACKLIST_WORDS else 'None'}

**📝 FILE NAMING**
👉 Prefix - Add text at START
   - Example: "[720p] " → "[720p] filename.mkv"
   - Current: {Config.FILE_PREFIX or 'None'}

👉 Suffix - Add text at END (before extension)
   - Example: " - HD" → "filename - HD.mkv"
   - Current: {Config.FILE_SUFFIX or 'None'}

👉 Remove Username (✅ {'ON' if Config.REMOVE_USERNAME else 'OFF'})
   - Removes @username patterns from filenames
   - Removes underscores FIRST, then @usernames
   - Then adds prefix/suffix
   - Order: Remove _ → Remove @xxx → Add prefix/suffix

**💬 CAPTION VARIABLES**
Add dynamic info to every file caption:
- {{filename}} - Processed filename (underscores removed, @username removed)
- {{filesize}} - File size (e.g., 1.5GB, 500MB)
- {{language}} - Detected language (English, Hindi, Tamil, Telugu, Kannada, Malayalam, Punjabi)
- {{subtitle}} - Subtitle type (Esub=English, Hsub=Hindi, Msub=Malayalam, Tsub=Tamil, Tesub=Telugu, Ksub=Kannada, Psub=Punjabi, or empty if no subtitle)
- {{filecaption}} - Original caption from source message

Example: 📥 {{filename}} | 🌍 {{language}} | 📝 {{subtitle}}
Current: {Config.CUSTOM_CAPTION or 'None'}

**🎬 THUMBNAIL**
- Optional: Set one image as thumbnail for all uploads
- Click "Set Thumbnail" and send a photo
- Will resize to 320x320
- Status: {'✅ Set' if has_thumbnail() else '❌ Not set'}

**📺 PREMIUM MODE** (✅ {'ON' if Config.PROCESS_ABOVE_2GB else 'OFF'})
- OFF: Skip files >2GB (Telegram free limit)
- ON: Process all files including >2GB (Telegram Premium)
- Files skipped show: "⏭️ SKIP: filename - ⚠️ NOT PREMIUM USER"

**⚡ PROCESS & MONITOR**
1️⃣ Setup all channels
2️⃣ Set message range
3️⃣ Configure filters (optional)
4️⃣ Click "Process"
5️⃣ Monitor real-time: download/upload %, speeds, queue
6️⃣ Use ⏸️ Pause, ▶️ Resume, 🛑 Cancel buttons

**📊 REAL-TIME STATUS DISPLAY**
- ⬇️ Download speed & percentage
- ⬆️ Upload progress & destination
- 📋 Next 5 queued files with sizes
- ⏸️ PAUSED indicator when paused
- File counts: (3/20) = 3 of 20 processed

**⚠️ IMPORTANT NOTES**
- Bot must be ADMIN in both channels
- Comma-separate multiple IDs: -1001, -1002, -1003
- Filters are CASE-INSENSITIVE
- Settings PERSIST across bot restarts
- All config saved automatically
        """
        await callback.message.edit_text(help_text, reply_markup=get_back_button())
        await callback.answer()
    
    @app.on_callback_query(filters.regex("^menu_setrange$") & owner_callback_filter)
    async def setrange_callback(client: Client, callback: CallbackQuery):
        user_id = callback.from_user.id
        if user_id not in user_data:
            user_data[user_id] = {}
        user_data[user_id]['waiting_for'] = 'range'
        user_data[user_id]['menu_message'] = callback.message
        
        await callback.message.edit_text(
            "**Set Message Range**\n\n"
            "Send me the start and end message links in this format:\n\n"
            "`<start_link> <end_link>`\n\n"
            "Example:\n"
            "`https://t.me/c/123456789/1 https://t.me/c/123456789/100`\n\n"
            "Or use command:\n"
            "/setrange <start_link> <end_link>",
            reply_markup=get_cancel_button()
        )
        await callback.answer()
    
    @app.on_callback_query(filters.regex("^menu_process$") & owner_callback_filter)
    async def process_callback(client: Client, callback: CallbackQuery):
        user_id = callback.from_user.id
        data = user_data.get(user_id, {})
        
        # Priority: Use DB range first, then session range
        start_link = Config.START_LINK or data.get('start_link')
        end_link = Config.END_LINK or data.get('end_link')
        
        if not start_link or not end_link:
            await callback.answer("Please set the range first!", show_alert=True)
            return
        
        if not Config.DESTINATION_CHANNEL_IDS:
            await callback.answer("No destination channels configured!", show_alert=True)
            return
        
        await callback.answer("Starting processing...")
        await callback.message.edit_text("Starting processing...")
        
        final_text = "Processing complete!"
        try:
            _, summary = await process_range(
                client,
                start_link,
                end_link,
                callback.message
            )
            final_text = summary
        except Exception as e:
            final_text = f"Error: {e}"
            await callback.message.edit_text(final_text)
        
        try:
            await callback.message.edit_text(final_text, reply_markup=get_main_menu())
        except:
            pass
    
    @app.on_callback_query(filters.regex("^set_source$") & owner_callback_filter)
    async def set_source_callback(client: Client, callback: CallbackQuery):
        user_id = callback.from_user.id
        if user_id not in user_data:
            user_data[user_id] = {}
        user_data[user_id]['waiting_for'] = 'source'
        user_data[user_id]['menu_message'] = callback.message
        
        current = format_channel_list(Config.SOURCE_CHANNEL_IDS)
        
        await callback.message.edit_text(
            f"**Set Source Channels**\n\n"
            f"Current: {current}\n\n"
            f"Send me the source channel ID(s).\n"
            f"For multiple channels, separate with commas.\n\n"
            f"Example:\n"
            f"`-1001234567890`\n"
            f"or\n"
            f"`-1001234567890, -1009876543210`\n\n"
            f"Or use command: /setsource <ids>",
            reply_markup=get_cancel_button()
        )
        await callback.answer()
    
    @app.on_callback_query(filters.regex("^set_dest$") & owner_callback_filter)
    async def set_dest_callback(client: Client, callback: CallbackQuery):
        user_id = callback.from_user.id
        if user_id not in user_data:
            user_data[user_id] = {}
        user_data[user_id]['waiting_for'] = 'dest'
        user_data[user_id]['menu_message'] = callback.message
        
        current = format_channel_list(Config.DESTINATION_CHANNEL_IDS)
        
        await callback.message.edit_text(
            f"**Set Destination Channels**\n\n"
            f"Current: {current}\n\n"
            f"Send me the destination channel ID(s).\n"
            f"For multiple channels, separate with commas.\n\n"
            f"Example:\n"
            f"`-1001234567890`\n"
            f"or\n"
            f"`-1001234567890, -1009876543210`\n\n"
            f"Or use command: /setdest <ids>",
            reply_markup=get_cancel_button()
        )
        await callback.answer()
    
    @app.on_callback_query(filters.regex("^set_whitelist$") & owner_callback_filter)
    async def set_whitelist_callback(client: Client, callback: CallbackQuery):
        user_id = callback.from_user.id
        if user_id not in user_data:
            user_data[user_id] = {}
        user_data[user_id]['waiting_for'] = 'whitelist'
        user_data[user_id]['menu_message'] = callback.message
        
        current = ', '.join(Config.WHITELIST_WORDS) if Config.WHITELIST_WORDS else 'None'
        
        await callback.message.edit_text(
            f"**Set Whitelist Words**\n\n"
            f"Current: {current}\n\n"
            f"Send me the whitelist words (comma-separated).\n"
            f"Only files containing these words will be processed.\n\n"
            f"Example:\n"
            f"`video, movie, episode`\n\n"
            f"Send `clear` to remove whitelist.",
            reply_markup=get_cancel_button()
        )
        await callback.answer()
    
    @app.on_callback_query(filters.regex("^set_blacklist$") & owner_callback_filter)
    async def set_blacklist_callback(client: Client, callback: CallbackQuery):
        user_id = callback.from_user.id
        if user_id not in user_data:
            user_data[user_id] = {}
        user_data[user_id]['waiting_for'] = 'blacklist'
        user_data[user_id]['menu_message'] = callback.message
        
        current = ', '.join(Config.BLACKLIST_WORDS) if Config.BLACKLIST_WORDS else 'None'
        
        await callback.message.edit_text(
            f"**Set Blacklist Words**\n\n"
            f"Current: {current}\n\n"
            f"Send me the blacklist words (comma-separated).\n"
            f"Files containing these words will be skipped.\n\n"
            f"Example:\n"
            f"`sample, trailer, teaser`\n\n"
            f"Send `clear` to remove blacklist.",
            reply_markup=get_cancel_button()
        )
        await callback.answer()
    
    @app.on_callback_query(filters.regex("^set_prefix$") & owner_callback_filter)
    async def set_prefix_callback(client: Client, callback: CallbackQuery):
        user_id = callback.from_user.id
        if user_id not in user_data:
            user_data[user_id] = {}
        user_data[user_id]['waiting_for'] = 'prefix'
        user_data[user_id]['menu_message'] = callback.message
        
        current = Config.FILE_PREFIX or 'None'
        
        await callback.message.edit_text(
            f"**Set File Prefix**\n\n"
            f"Current: {current}\n\n"
            f"Send me the prefix to add to file names.\n\n"
            f"Example:\n"
            f"`[MyChannel] `\n\n"
            f"Send `clear` to remove prefix.",
            reply_markup=get_cancel_button()
        )
        await callback.answer()
    
    @app.on_callback_query(filters.regex("^set_suffix$") & owner_callback_filter)
    async def set_suffix_callback(client: Client, callback: CallbackQuery):
        user_id = callback.from_user.id
        if user_id not in user_data:
            user_data[user_id] = {}
        user_data[user_id]['waiting_for'] = 'suffix'
        user_data[user_id]['menu_message'] = callback.message
        
        current = Config.FILE_SUFFIX or 'None'
        
        await callback.message.edit_text(
            f"**Set File Suffix**\n\n"
            f"Current: {current}\n\n"
            f"Send me the suffix to add to file names.\n\n"
            f"Example:\n"
            f"` - HD`\n\n"
            f"Send `clear` to remove suffix.",
            reply_markup=get_cancel_button()
        )
        await callback.answer()
    
    @app.on_callback_query(filters.regex("^set_thumb$") & owner_callback_filter)
    async def set_thumb_callback(client: Client, callback: CallbackQuery):
        user_id = callback.from_user.id
        if user_id not in user_data:
            user_data[user_id] = {}
        user_data[user_id]['waiting_for'] = 'thumb'
        user_data[user_id]['menu_message'] = callback.message
        
        await callback.message.edit_text(
            "**Set Thumbnail**\n\n"
            "Send me a photo to use as thumbnail for uploads.\n\n"
            "The thumbnail will be resized to 320x320.",
            reply_markup=get_cancel_button()
        )
        await callback.answer()
    
    @app.on_callback_query(filters.regex("^del_thumb$") & owner_callback_filter)
    async def del_thumb_callback(client: Client, callback: CallbackQuery):
        if delete_thumbnail():
            await callback.answer("Thumbnail deleted!", show_alert=True)
            await callback.message.edit_text(get_settings_text(), reply_markup=get_settings_menu())
        else:
            await callback.answer("No thumbnail to delete.", show_alert=True)
    
    @app.on_callback_query(filters.regex("^send_thumb$") & owner_callback_filter)
    async def send_thumb_callback(client: Client, callback: CallbackQuery):
        thumb_path = get_thumbnail()
        if thumb_path and os.path.exists(thumb_path):
            try:
                with open(thumb_path, 'rb') as photo_file:
                    await client.send_photo(
                        callback.from_user.id,
                        photo_file,
                        caption="📸 Your current thumbnail (320x320)\n\nThis is your thumbnail that will be used for all uploads"
                    )
                await callback.answer("✅ Thumbnail sent to your chat!")
            except Exception as e:
                print(f"Error sending thumbnail: {e}")
                await callback.answer(f"❌ Error sending thumbnail", show_alert=True)
        else:
            await callback.answer("❌ No thumbnail set!", show_alert=True)
    
    @app.on_callback_query(filters.regex("^reset_all$") & owner_callback_filter)
    async def reset_all_callback(client: Client, callback: CallbackQuery):
        user_id = callback.from_user.id
        if user_id not in user_data:
            user_data[user_id] = {}
        user_data[user_id]['waiting_for'] = 'confirm_reset'
        
        await callback.message.edit_text(
            "⚠️ **RESET ALL SETTINGS?**\n\n"
            "This will reset ALL configuration to default:\n"
            "❌ Source & Destination channels\n"
            "❌ Filters (whitelist/blacklist)\n"
            "❌ Prefix & Suffix\n"
            "❌ Custom caption\n"
            "❌ Thumbnail\n"
            "❌ Premium mode\n"
            "❌ Username removal\n\n"
            "Type **YES** to confirm reset\n"
            "Type anything else to cancel",
            reply_markup=get_cancel_button()
        )
        await callback.answer()
    
    @app.on_message(filters.private & owner_filter & filters.regex("^(YES|yes|Yes)$"))
    async def confirm_reset(client: Client, message: Message):
        user_id = message.from_user.id
        data = user_data.get(user_id, {})
        if data.get('waiting_for') != 'confirm_reset':
            return
        
        # Reset all settings
        Config.SOURCE_CHANNEL_IDS = []
        Config.DESTINATION_CHANNEL_IDS = []
        Config.WHITELIST_WORDS = []
        Config.BLACKLIST_WORDS = []
        Config.FILE_PREFIX = ""
        Config.FILE_SUFFIX = ""
        Config.REMOVE_USERNAME = False
        Config.CUSTOM_CAPTION = ""
        Config.START_LINK = None
        Config.END_LINK = None
        Config.PROCESS_ABOVE_2GB = False
        delete_thumbnail()
        
        # Reset in database
        await update_setting("source_channels", [])
        await update_setting("destination_channels", [])
        await update_setting("whitelist_words", [])
        await update_setting("blacklist_words", [])
        await update_setting("file_prefix", "")
        await update_setting("file_suffix", "")
        await update_setting("remove_username", False)
        await update_setting("custom_caption", "")
        await update_setting("start_link", None)
        await update_setting("end_link", None)
        await update_setting("process_above_2gb", False)
        
        user_data[user_id]['waiting_for'] = None
        
        await message.reply_text(
            "✅ **ALL SETTINGS RESET TO DEFAULT**\n\n"
            "All configuration has been cleared.\n"
            "Start fresh by configuring channels and filters.",
            reply_markup=get_main_menu()
        )
        try:
            await message.delete()
        except:
            pass
    
    @app.on_callback_query(filters.regex("^toggle_remove_username$") & owner_callback_filter)
    async def toggle_remove_username_callback(client: Client, callback: CallbackQuery):
        Config.REMOVE_USERNAME = not Config.REMOVE_USERNAME
        await update_setting("remove_username", Config.REMOVE_USERNAME)
        status = "✅ ON" if Config.REMOVE_USERNAME else "❌ OFF"
        await callback.answer(f"Username removal {status}", show_alert=True)
        await callback.message.edit_text(get_settings_text(), reply_markup=get_settings_menu())
    
    @app.on_callback_query(filters.regex("^toggle_premium$") & owner_callback_filter)
    async def toggle_premium_callback(client: Client, callback: CallbackQuery):
        Config.PROCESS_ABOVE_2GB = not Config.PROCESS_ABOVE_2GB
        await update_setting("process_above_2gb", Config.PROCESS_ABOVE_2GB)
        status = "✅ ON" if Config.PROCESS_ABOVE_2GB else "❌ OFF"
        await callback.answer(f"Premium mode (>2GB) {status}", show_alert=True)
        await callback.message.edit_text(get_settings_text(), reply_markup=get_settings_menu())
    
    @app.on_callback_query(filters.regex("^set_caption$") & owner_callback_filter)
    async def set_caption_callback(client: Client, callback: CallbackQuery):
        user_id = callback.from_user.id
        if user_id not in user_data:
            user_data[user_id] = {}
        user_data[user_id]['waiting_for'] = 'caption'
        user_data[user_id]['menu_message'] = callback.message
        
        current = Config.CUSTOM_CAPTION or 'None'
        
        await callback.message.edit_text(
            f"**Set Custom Caption**\n\n"
            f"Current: {current}\n\n"
            f"**Available Variables (Like Leech Bot):**\n"
            f"• {{filename}} - Processed file name with extension\n"
            f"• {{filesize}} - File size (e.g., 1.5GB, 500MB)\n"
            f"• {{filecaption}} - Original caption from source\n"
            f"• {{language}} - Detected language (English, Hindi, Tamil, etc.)\n"
            f"• {{subtitle}} - Subtitle type (Esub, Hsub, Msub, Tsub, etc.)\n\n"
            f"**Example Caption #1 (Basic):**\n"
            f"`📥 {{filename}}\n"
            f"💾 Size: {{filesize}}\n"
            f"📝 {{filecaption}}`\n\n"
            f"**Example Caption #2 (With Language & Subtitle):**\n"
            f"`📥 {{filename}}\n"
            f"💾 Size: {{filesize}}\n"
            f"🌍 {{language}} | 📝 {{subtitle}}\n"
            f"ℹ️ {{filecaption}}`\n\n"
            f"Send `clear` to remove caption.",
            reply_markup=get_cancel_button()
        )
        await callback.answer()
    
    @app.on_message(filters.private & owner_filter & ~filters.command(["start", "help", "status", "setrange", "process", "setthumb", "delthumb", "setwhitelist", "setblacklist", "setsource", "setdest", "setprefix", "setsuffix", "restart"]))
    async def handle_user_input(client: Client, message: Message):
        user_id = message.from_user.id
        data = user_data.get(user_id, {})
        waiting_for = data.get('waiting_for')
        menu_message = data.get('menu_message')
        
        if not waiting_for:
            return
        
        text = message.text or ""
        
        async def update_menu(new_text: str, markup):
            if menu_message:
                try:
                    await menu_message.edit_text(new_text, reply_markup=markup)
                    try:
                        await message.delete()
                    except:
                        pass
                    return
                except:
                    pass
            await message.reply_text(new_text, reply_markup=markup)
        
        def get_prompt_template(prompt_type: str) -> str:
            templates = {
                'range': "**Set Message Range**\n\nSend me start and end links separated by space.",
                'source': f"**Set Source Channels**\n\nCurrent: {format_channel_list(Config.SOURCE_CHANNEL_IDS)}\n\nSend channel IDs (e.g., -100XXXXXXXXXX)",
                'dest': f"**Set Destination Channels**\n\nCurrent: {format_channel_list(Config.DESTINATION_CHANNEL_IDS)}\n\nSend channel IDs (e.g., -100XXXXXXXXXX)",
                'whitelist': f"**Set Whitelist**\n\nCurrent: {', '.join(Config.WHITELIST_WORDS) if Config.WHITELIST_WORDS else 'None'}\n\nSend words (comma-separated) or 'clear'",
                'blacklist': f"**Set Blacklist**\n\nCurrent: {', '.join(Config.BLACKLIST_WORDS) if Config.BLACKLIST_WORDS else 'None'}\n\nSend words (comma-separated) or 'clear'",
                'prefix': f"**Set Prefix**\n\nCurrent: {Config.FILE_PREFIX or 'None'}\n\nSend prefix text or 'clear'",
                'suffix': f"**Set Suffix**\n\nCurrent: {Config.FILE_SUFFIX or 'None'}\n\nSend suffix text or 'clear'",
                'thumb': "**Set Thumbnail**\n\nSend a photo to use as thumbnail."
            }
            return templates.get(prompt_type, "")
        
        async def show_error(error_text: str):
            prompt = get_prompt_template(waiting_for) if waiting_for else ""
            error_msg = f"{prompt}\n\n**Error:** {error_text}" if prompt else error_text
            
            if menu_message:
                try:
                    await menu_message.edit_text(error_msg, reply_markup=get_cancel_button())
                    try:
                        await message.delete()
                    except:
                        pass
                    return
                except:
                    pass
            await message.reply_text(error_text, reply_markup=get_cancel_button())
        
        if waiting_for == 'range':
            parts = text.split()
            if len(parts) == 2:
                user_data[user_id]['start_link'] = parts[0]
                user_data[user_id]['end_link'] = parts[1]
                Config.START_LINK = parts[0]
                Config.END_LINK = parts[1]
                await update_setting("start_link", parts[0])
                await update_setting("end_link", parts[1])
                user_data[user_id]['waiting_for'] = None
                await update_menu(
                    f"Range set!\n\n"
                    f"Start: {parts[0]}\n"
                    f"End: {parts[1]}",
                    get_main_menu()
                )
            else:
                await show_error("Please send two links separated by space.")
        
        elif waiting_for == 'source':
            channels, error = parse_channel_ids(text)
            if error:
                await show_error(f"{error}\n\nPlease send valid channel IDs like `-100XXXXXXXXXX`")
            elif channels:
                Config.SOURCE_CHANNEL_IDS = channels
                await update_setting("source_channels", channels)
                user_data[user_id]['waiting_for'] = None
                await update_menu(get_settings_text(), get_settings_menu())
            else:
                await show_error("No valid channels found.")
        
        elif waiting_for == 'dest':
            channels, error = parse_channel_ids(text)
            if error:
                await show_error(f"{error}\n\nPlease send valid channel IDs like `-100XXXXXXXXXX`")
            elif channels:
                Config.DESTINATION_CHANNEL_IDS = channels
                await update_setting("destination_channels", channels)
                user_data[user_id]['waiting_for'] = None
                await update_menu(get_settings_text(), get_settings_menu())
            else:
                await show_error("No valid channels found.")
        
        elif waiting_for == 'whitelist':
            user_data[user_id]['waiting_for'] = None
            if text.lower() == 'clear':
                Config.WHITELIST_WORDS = []
                await update_setting("whitelist_words", [])
            else:
                words = [w.strip().lower() for w in text.split(",") if w.strip()]
                Config.WHITELIST_WORDS = words
                await update_setting("whitelist_words", words)
            await update_menu(get_settings_text(), get_settings_menu())
        
        elif waiting_for == 'blacklist':
            user_data[user_id]['waiting_for'] = None
            if text.lower() == 'clear':
                Config.BLACKLIST_WORDS = []
                await update_setting("blacklist_words", [])
            else:
                words = [w.strip().lower() for w in text.split(",") if w.strip()]
                Config.BLACKLIST_WORDS = words
                await update_setting("blacklist_words", words)
            await update_menu(get_settings_text(), get_settings_menu())
        
        elif waiting_for == 'prefix':
            user_data[user_id]['waiting_for'] = None
            if text.lower() == 'clear':
                Config.FILE_PREFIX = ""
                await update_setting("file_prefix", "")
            else:
                Config.FILE_PREFIX = text
                await update_setting("file_prefix", text)
            await update_menu(get_settings_text(), get_settings_menu())
        
        elif waiting_for == 'suffix':
            user_data[user_id]['waiting_for'] = None
            if text.lower() == 'clear':
                Config.FILE_SUFFIX = ""
                await update_setting("file_suffix", "")
            else:
                Config.FILE_SUFFIX = text
                await update_setting("file_suffix", text)
            await update_menu(get_settings_text(), get_settings_menu())
        
        elif waiting_for == 'caption':
            user_data[user_id]['waiting_for'] = None
            if text.lower() == 'clear':
                Config.CUSTOM_CAPTION = ""
                await update_setting("custom_caption", "")
            else:
                Config.CUSTOM_CAPTION = text
                await update_setting("custom_caption", text)
            await update_menu(get_settings_text(), get_settings_menu())
        
        elif waiting_for == 'removed_words':
            user_data[user_id]['waiting_for'] = None
            if text.lower() == 'clear':
                Config.REMOVED_WORDS = []
                await update_setting("removed_words", [])
            else:
                # APPEND new words to existing list (don't replace)
                new_words = [w.strip() for w in text.split(",") if w.strip()]
                Config.REMOVED_WORDS.extend(new_words)
                # Remove duplicates while preserving order
                Config.REMOVED_WORDS = list(dict.fromkeys(Config.REMOVED_WORDS))
                await update_setting("removed_words", Config.REMOVED_WORDS)
            await update_menu(get_settings_text(), get_settings_menu())
        
        elif waiting_for == 'thumb':
            if message.photo:
                temp_path = os.path.join(Config.DOWNLOAD_DIR, "temp_thumb.jpg")
                os.makedirs(Config.DOWNLOAD_DIR, exist_ok=True)
                await client.download_media(message, file_name=temp_path)
                
                if save_thumbnail(temp_path):
                    user_data[user_id]['waiting_for'] = None
                    await update_menu(get_settings_text(), get_settings_menu())
                else:
                    await show_error("Failed to save thumbnail.")
                
                try:
                    os.remove(temp_path)
                except:
                    pass
            else:
                await show_error("Please send a photo.")
    
    @app.on_message(filters.command("help") & filters.private)
    async def help_command(client: Client, message: Message):
        help_text = """
**Channel File Processor Bot - Complete Guide**

**📥 CORE FEATURES:**

🔹 **Source Channels** - Download files from these channels
   /setsource -1001234567890
   Can set multiple channels comma-separated

🔹 **Destination Channels** - Upload processed files to these channels
   /setdest -1001234567890
   Can set multiple channels comma-separated

📋 **Message Range** - Process only messages between start and end links
   /setrange <start_link> <end_link>
   Example: /setrange https://t.me/c/123/1 https://t.me/c/123/50

**🔧 FILE PROCESSING:**

✂️ **Remove Words** - Remove specific words from filenames (case-sensitive)
   Example: Remove "IL" from "IL_Movie.mkv" → "Movie.mkv"
   Use button in Settings, type comma-separated words
   Exact match only (IL ≠ il)

🏷️ **Prefix/Suffix** - Add text before/after filename
   /setprefix [MOVIE]
   /setsuffix [720p]
   Example: [MOVIE] Filename [720p].mkv

👤 **Username Removal** - Automatically remove @usernames from anywhere
   ON: @user_George.mkv → George.mkv
   OFF: @user_George.mkv → @user_George.mkv

**🚫 FILTERING:**

🔹 **Whitelist** - Only process files containing these words
   /setwhitelist tamil, english
   Only downloads matching these words

🔹 **Blacklist** - Skip files containing these words
   /setblacklist trailer, promo
   Never downloads matching these words

**💬 CUSTOM CAPTION:**
Add captions when uploading with variables:
- {{filename}} - Processed filename
- {{filesize}} - File size
- {{filecaption}} - Original caption
- {{language}} - Detected language
- {{subtitle}} - Subtitle info

**🎨 ADVANCED:**

📸 **Thumbnail** - Set custom thumbnail for uploads
   /setthumb (reply to a photo)
   /delthumb (remove thumbnail)

⭐ **Premium Mode** - Handle files >2GB
   Requires Telegram Premium in bot account
   Enable via Settings → Premium Mode

⚙️ **Parallel Downloads** - Concurrent file processing (1-5)
   1 = Sequential, 5 = Maximum speed
   Set via Settings → Parallel Setting

**💾 BACKUP & RESTORE:**

📤 **Backup Settings** - Export all 13 settings as JSON
📥 **Restore Settings** - Import settings from backup JSON

**🎯 PROCESSING:**

/process - Start downloading and uploading files
/status - View real-time progress
🛑 Cancel - Stop processing

**⚡ QUICK COMMANDS:**
/start - Main menu
/help - This guide
/status - Current status
/restart - Restart bot with settings saved

**💡 TIPS:**
✓ Use Settings button for easier navigation
✓ All settings saved automatically to database
✓ Bot must be admin in all channels
✓ Separate multiple IDs with commas
✓ Remove Words works case-sensitively (exact match)
✓ Backup settings regularly for safety
        """
        await message.reply_text(help_text, reply_markup=get_main_menu())
    
    @app.on_message(filters.command("status") & filters.private & owner_filter)
    async def status_command(client: Client, message: Message):
        if current_status['status'] != 'idle':
            await message.reply_text(get_status_text(), reply_markup=get_process_control_buttons())
        else:
            await message.reply_text(get_status_text())
    
    @app.on_message(filters.command("setsource") & filters.private & owner_filter)
    async def setsource_command(client: Client, message: Message):
        args = message.text.split(maxsplit=1)
        
        if len(args) < 2:
            await message.reply_text(
                "Usage: /setsource <channel_ids>\n\n"
                "Example:\n"
                "/setsource -1001234567890\n"
                "/setsource -1001234567890, -1009876543210"
            )
            return
        
        channels, error = parse_channel_ids(args[1])
        if error:
            await message.reply_text(f"Invalid input: {error}")
            return
        
        if channels:
            Config.SOURCE_CHANNEL_IDS = channels
            await message.reply_text(
                f"Source channels set!\n\n{format_channel_list(channels)}",
                reply_markup=get_main_menu()
            )
        else:
            await message.reply_text("No valid channels found.")
    
    @app.on_message(filters.command("setdest") & filters.private & owner_filter)
    async def setdest_command(client: Client, message: Message):
        args = message.text.split(maxsplit=1)
        
        if len(args) < 2:
            await message.reply_text(
                "Usage: /setdest <channel_ids>\n\n"
                "Example:\n"
                "/setdest -1001234567890\n"
                "/setdest -1001234567890, -1009876543210"
            )
            return
        
        channels, error = parse_channel_ids(args[1])
        if error:
            await message.reply_text(f"Invalid input: {error}")
            return
        
        if channels:
            Config.DESTINATION_CHANNEL_IDS = channels
            await message.reply_text(
                f"Destination channels set!\n\n{format_channel_list(channels)}",
                reply_markup=get_main_menu()
            )
        else:
            await message.reply_text("No valid channels found.")
    
    @app.on_message(filters.command("setrange") & filters.private & owner_filter)
    async def setrange_command(client: Client, message: Message):
        args = message.text.split()[1:]
        
        if len(args) != 2:
            await message.reply_text(
                "Usage: /setrange <start_link> <end_link>\n\n"
                "Example:\n"
                "/setrange https://t.me/c/123456789/1 https://t.me/c/123456789/100"
            )
            return
        
        start_link, end_link = args
        user_id = message.from_user.id
        
        if user_id not in user_data:
            user_data[user_id] = {}
        
        user_data[user_id]['start_link'] = start_link
        user_data[user_id]['end_link'] = end_link
        
        # Ask user if they want to store this in database
        range_msg = (
            f"📋 **Message Range Set:**\n\n"
            f"Start: {start_link}\n"
            f"End: {end_link}\n\n"
            "💾 **Store this range in database?**\n"
            "(You can use it later after restart)"
        )
        
        store_buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("💾 Store", callback_data="store_range_yes"),
             InlineKeyboardButton("❌ Don't Store", callback_data="store_range_no")]
        ])
        
        await message.reply_text(range_msg, reply_markup=store_buttons)
    
    @app.on_message(filters.command("process") & filters.private & owner_filter)
    async def process_command(client: Client, message: Message):
        user_id = message.from_user.id
        data = user_data.get(user_id, {})
        
        # Priority: Use DB range first, then session range
        start_link = Config.START_LINK or data.get('start_link')
        end_link = Config.END_LINK or data.get('end_link')
        
        if not start_link or not end_link:
            await message.reply_text(
                "Please set the range first using:\n"
                "/setrange <start_link> <end_link>"
            )
            return
        
        if not Config.DESTINATION_CHANNEL_IDS:
            await message.reply_text(
                "No destination channels configured!\n"
                "Use /setdest or Settings > Dest Channels"
            )
            return
        
        status_msg = await message.reply_text("Starting processing...")
        
        final_text = "Processing complete!"
        try:
            _, summary = await process_range(
                client,
                start_link,
                end_link,
                status_msg
            )
            final_text = summary
        except Exception as e:
            final_text = f"Error: {e}"
            await status_msg.edit_text(final_text)
        
        try:
            await status_msg.edit_text(final_text, reply_markup=get_main_menu())
        except:
            pass
    
    @app.on_message(filters.command("setthumb") & filters.private & owner_filter)
    async def setthumb_command(client: Client, message: Message):
        if not message.reply_to_message or not message.reply_to_message.photo:
            await message.reply_text(
                "Please reply to a photo with /setthumb to set it as thumbnail."
            )
            return
        
        status_msg = await message.reply_text("Saving thumbnail...")
        
        try:
            photo = message.reply_to_message
            temp_path = os.path.join(Config.DOWNLOAD_DIR, "temp_thumb.jpg")
            os.makedirs(Config.DOWNLOAD_DIR, exist_ok=True)
            
            await client.download_media(photo, file_name=temp_path)
            
            if save_thumbnail(temp_path):
                await status_msg.edit_text("Thumbnail saved!", reply_markup=get_main_menu())
            else:
                await status_msg.edit_text("Failed to save thumbnail.")
            
            try:
                os.remove(temp_path)
            except:
                pass
                
        except Exception as e:
            await status_msg.edit_text(f"Error: {e}")
    
    @app.on_message(filters.command("delthumb") & filters.private & owner_filter)
    async def delthumb_command(client: Client, message: Message):
        if delete_thumbnail():
            await message.reply_text("Thumbnail deleted.", reply_markup=get_main_menu())
        else:
            await message.reply_text("No thumbnail to delete.")
    
    @app.on_message(filters.command("setwhitelist") & filters.private & owner_filter)
    async def setwhitelist_command(client: Client, message: Message):
        args = message.text.split(maxsplit=1)
        
        if len(args) < 2:
            await message.reply_text(
                "Usage: /setwhitelist word1, word2, word3\n\n"
                "Send 'clear' to remove whitelist."
            )
            return
        
        if args[1].lower() == 'clear':
            Config.WHITELIST_WORDS = []
            await message.reply_text("Whitelist cleared!", reply_markup=get_main_menu())
        else:
            words = [w.strip().lower() for w in args[1].split(",") if w.strip()]
            Config.WHITELIST_WORDS = words
            await message.reply_text(f"Whitelist set: {', '.join(words)}", reply_markup=get_main_menu())
    
    @app.on_message(filters.command("setblacklist") & filters.private & owner_filter)
    async def setblacklist_command(client: Client, message: Message):
        args = message.text.split(maxsplit=1)
        
        if len(args) < 2:
            await message.reply_text(
                "Usage: /setblacklist word1, word2, word3\n\n"
                "Send 'clear' to remove blacklist."
            )
            return
        
        if args[1].lower() == 'clear':
            Config.BLACKLIST_WORDS = []
            await message.reply_text("Blacklist cleared!", reply_markup=get_main_menu())
        else:
            words = [w.strip().lower() for w in args[1].split(",") if w.strip()]
            Config.BLACKLIST_WORDS = words
            await message.reply_text(f"Blacklist set: {', '.join(words)}", reply_markup=get_main_menu())
    
    @app.on_callback_query(filters.regex("^set_removed_words$") & owner_callback_filter)
    async def set_removed_words_callback(client: Client, callback: CallbackQuery):
        """Handle set removed words button click"""
        user_id = callback.from_user.id
        if user_id not in user_data:
            user_data[user_id] = {}
        user_data[user_id]['waiting_for'] = 'removed_words'
        user_data[user_id]['menu_message'] = callback.message
        
        buttons = []
        # Add clear all button if there are words
        if Config.REMOVED_WORDS:
            buttons.append([InlineKeyboardButton("🗑️ Clear All Words", callback_data="clear_all_words")])
        
        buttons.append([InlineKeyboardButton("Back to Menu", callback_data="menu_settings")])
        
        msg_text = (
            "✂️ **Remove Words from Filename**\n\n"
            f"Current Words: {', '.join(Config.REMOVED_WORDS) if Config.REMOVED_WORDS else 'None'}\n\n"
            "📌 **How to Use:**\n"
            "• Send new words (comma-separated) to ADD them to the list\n"
            "• Click 'Clear All Words' to empty the list\n\n"
            "Example: IL, xyz, test"
        )
        
        await callback.message.edit_text(
            msg_text,
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        await callback.answer()
    
    
    @app.on_callback_query(filters.regex("^clear_all_words$") & owner_callback_filter)
    async def clear_all_words_callback(client: Client, callback: CallbackQuery):
        """Clear all removed words"""
        Config.REMOVED_WORDS = []
        await update_setting("removed_words", [])
        
        user_id = callback.from_user.id
        if user_id not in user_data:
            user_data[user_id] = {}
        user_data[user_id]['waiting_for'] = None
        
        msg_text = (
            "✂️ **Remove Words from Filename**\n\n"
            f"Current Words: None\n\n"
            "📌 **How to Use:**\n"
            "• Send new words (comma-separated) to ADD them to the list\n"
            "• Click word buttons to remove individual words\n"
            "• Click 'Clear All Words' to empty the list\n\n"
            "Example: IL, xyz, test"
        )
        
        await callback.message.edit_text(
            msg_text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Back to Menu", callback_data="menu_settings")]
            ])
        )
        await callback.answer("✅ All words cleared!")
    
    @app.on_message(filters.command("setprefix") & filters.private & owner_filter)
    async def setprefix_command(client: Client, message: Message):
        args = message.text.split(maxsplit=1)
        
        if len(args) < 2:
            await message.reply_text("Usage: /setprefix <text>\n\nSend 'clear' to remove.")
            return
        
        if args[1].lower() == 'clear':
            Config.FILE_PREFIX = ""
            await message.reply_text("Prefix cleared!", reply_markup=get_main_menu())
        else:
            Config.FILE_PREFIX = args[1]
            await message.reply_text(f"Prefix set: `{args[1]}`", reply_markup=get_main_menu())
    
    @app.on_message(filters.command("setsuffix") & filters.private & owner_filter)
    async def setsuffix_command(client: Client, message: Message):
        args = message.text.split(maxsplit=1)
        
        if len(args) < 2:
            await message.reply_text("Usage: /setsuffix <text>\n\nSend 'clear' to remove.")
            return
        
        if args[1].lower() == 'clear':
            Config.FILE_SUFFIX = ""
            await message.reply_text("Suffix cleared!", reply_markup=get_main_menu())
        else:
            Config.FILE_SUFFIX = args[1]
            await message.reply_text(f"Suffix set: `{args[1]}`", reply_markup=get_main_menu())
    
    @app.on_callback_query(filters.regex("^range_confirmed$") & owner_callback_filter)
    async def range_confirmed_callback(client: Client, callback: CallbackQuery):
        await callback.message.edit_text("✅ **Range confirmed!** Ready to process.", reply_markup=get_main_menu())
        await callback.answer()
    
    @app.on_callback_query(filters.regex("^store_range_yes$") & owner_callback_filter)
    async def store_range_yes_callback(client: Client, callback: CallbackQuery):
        user_id = callback.from_user.id
        data = user_data.get(user_id, {})
        
        if 'start_link' in data and 'end_link' in data:
            Config.START_LINK = data['start_link']
            Config.END_LINK = data['end_link']
            
            from bot.database import update_setting
            await update_setting("start_link", Config.START_LINK)
            await update_setting("end_link", Config.END_LINK)
            
            # Save message to edit with process status
            save_msg = await callback.message.edit_text(
                f"✅ **Range Saved to Database!**\n\n"
                f"Start: {Config.START_LINK}\n"
                f"End: {Config.END_LINK}\n\n"
                f"🚀 Starting processing...",
                reply_markup=None
            )
            
            # Auto-execute process with the saved range
            await callback.answer()
            
            if not Config.DESTINATION_CHANNEL_IDS:
                await save_msg.edit_text(
                    "❌ No destination channels configured!\n"
                    "Please set destination channels first.",
                    reply_markup=get_main_menu()
                )
                return
            
            final_text = "Processing complete!"
            try:
                _, summary = await process_range(
                    client,
                    Config.START_LINK,
                    Config.END_LINK,
                    save_msg
                )
                final_text = summary
            except Exception as e:
                final_text = f"Error: {e}"
                await save_msg.edit_text(final_text)
            
            try:
                await save_msg.edit_text(final_text, reply_markup=get_main_menu())
            except:
                pass
        else:
            await callback.message.edit_text("❌ No range data found", reply_markup=get_main_menu())
            await callback.answer()
    
    @app.on_callback_query(filters.regex("^store_range_no$") & owner_callback_filter)
    async def store_range_no_callback(client: Client, callback: CallbackQuery):
        user_id = callback.from_user.id
        data = user_data.get(user_id, {})
        
        await callback.message.edit_text(
            f"❌ **Range Not Saved**\n\n"
            f"Start: {data.get('start_link', 'Not set')}\n"
            f"End: {data.get('end_link', 'Not set')}\n\n"
            "Range is set in memory for this session only.\n"
            "Use /setrange again to save to database.",
            reply_markup=get_main_menu()
        )
        await callback.answer()
    
    @app.on_callback_query(filters.regex("^cancel_all_now$") & owner_callback_filter)
    async def cancel_all_callback(client: Client, callback: CallbackQuery):
        current_status['cancel_all'] = True
        current_status['cancel_current_file'] = True
        await callback.answer()
        
        # Delete downloaded files
        try:
            import shutil
            dl_dir = Config.DOWNLOAD_DIR
            if os.path.exists(dl_dir):
                shutil.rmtree(dl_dir)
                os.makedirs(dl_dir, exist_ok=True)
        except Exception as e:
            print(f"Error deleting downloads: {e}")
        
        try:
            await callback.message.delete()
        except:
            pass
        
        try:
            await callback.message.reply_text("❌ Task Cancelled")
        except:
            pass
        
        # Auto-restart in background after 1 second
        async def auto_restart():
            await asyncio.sleep(1)
            current_status['status'] = 'idle'
            current_status['file_name'] = None
            current_status['cancel_all'] = False
            current_status['cancel_current_file'] = False
            current_status['processed'] = 0
            current_status['total'] = 0
            current_status['queue'] = []
        
        asyncio.create_task(auto_restart())
    
    @app.on_message(filters.command("restart") & filters.private & owner_filter)
    async def restart_command(client: Client, message: Message):
        global user_data
        
        # Step 1: Show "Bot is now restarting" message
        restart_msg = None
        try:
            restart_msg = await message.reply_text("🔄 **Bot is now restarting...**")
        except:
            pass
        
        # Step 2: Refresh all state (graceful reload)
        await asyncio.sleep(0.5)
        
        # Clear user session data
        user_data.clear()
        
        # Reset processing status
        current_status['status'] = 'idle'
        current_status['file_name'] = None
        current_status['paused'] = False
        current_status['cancel_all'] = False
        current_status['cancel_current_file'] = False
        current_status['processed'] = 0
        current_status['total'] = 0
        current_status['queue'] = []
        
        # Reload settings from database
        from bot.database import load_settings_sync
        settings = load_settings_sync()
        Config.SOURCE_CHANNEL_IDS = settings.get("source_channels", [])
        Config.DESTINATION_CHANNEL_IDS = settings.get("destination_channels", [])
        Config.WHITELIST_WORDS = settings.get("whitelist_words", [])
        Config.BLACKLIST_WORDS = settings.get("blacklist_words", [])
        Config.FILE_PREFIX = settings.get("file_prefix", "")
        Config.FILE_SUFFIX = settings.get("file_suffix", "")
        Config.REMOVE_USERNAME = settings.get("remove_username", False)
        Config.CUSTOM_CAPTION = settings.get("custom_caption", "")
        Config.START_LINK = settings.get("start_link")
        Config.END_LINK = settings.get("end_link")
        Config.PROCESS_ABOVE_2GB = settings.get("process_above_2gb", False)
        
        # Step 3: Delete the restarting message and send success message
        if restart_msg:
            try:
                await restart_msg.delete()
            except:
                pass
        
        try:
            await message.reply_text("✅ **Successfully restarted!**\n\nAll settings reloaded.\nBot is ready to use.", reply_markup=get_main_menu())
        except:
            pass
    
    
    @app.on_callback_query(filters.regex("^export_settings$") & owner_callback_filter)
    async def export_settings_callback(client: Client, callback: CallbackQuery):
        """Backup all bot settings to MongoDB"""
        try:
            settings_data = {
                "source_channels": Config.SOURCE_CHANNEL_IDS,
                "destination_channels": Config.DESTINATION_CHANNEL_IDS,
                "whitelist_words": Config.WHITELIST_WORDS,
                "blacklist_words": Config.BLACKLIST_WORDS,
                "file_prefix": Config.FILE_PREFIX,
                "file_suffix": Config.FILE_SUFFIX,
                "remove_username": Config.REMOVE_USERNAME,
                "custom_caption": Config.CUSTOM_CAPTION,
                "process_above_2gb": Config.PROCESS_ABOVE_2GB,
                
                "start_link": Config.START_LINK,
                "end_link": Config.END_LINK
            }
            
            # Save to MongoDB backup
            await callback.message.edit_text("💾 **Saving backup...**")
            await save_backup(settings_data)
            
            # Show success message
            success_msg = (
                "✅ **Settings Backed Up Successfully!**\n\n"
                f"📁 Source Channels: {len(Config.SOURCE_CHANNEL_IDS)}\n"
                f"📤 Dest Channels: {len(Config.DESTINATION_CHANNEL_IDS)}\n"
                f"✔️ Whitelist: {len(Config.WHITELIST_WORDS)} words\n"
                f"❌ Blacklist: {len(Config.BLACKLIST_WORDS)} words\n"
                f"\nYou can restore these settings anytime using the Restore Settings button."
            )
            await callback.message.edit_text(success_msg, reply_markup=get_settings_menu())
            await callback.answer("✅ Backup created!")
                
        except Exception as e:
            await callback.answer(f"❌ Error: {e}", show_alert=True)
    
    @app.on_callback_query(filters.regex("^restore_settings$") & owner_callback_filter)
    async def restore_settings_callback(client: Client, callback: CallbackQuery):
        """Show backup settings as TEXT with Edit & Confirm options"""
        try:
            user_id = callback.from_user.id
            if user_id not in user_data:
                user_data[user_id] = {}
            
            await callback.message.edit_text("⏳ **Loading backup...**")
            
            # Load backup from MongoDB
            backup_data = await load_backup()
            
            if not backup_data:
                await callback.message.edit_text(
                    "❌ **No backup found!**\n\nPlease backup your settings first using 📤 Backup Settings button.",
                    reply_markup=get_settings_menu()
                )
                await callback.answer()
                return
            
            # Store backup data for editing
            user_data[user_id]['backup_data'] = backup_data
            user_data[user_id]['waiting_for'] = 'restore_confirm'
            
            # Format settings as JSON text
            backup_json = json.dumps(backup_data, indent=2)
            
            # Show as text with Edit & Confirm buttons
            text_msg = f"""📋 **Backed-up Settings (JSON)**

```json
{backup_json}
```

**Options:**
- Click ✏️ Edit to paste edited JSON
- Click ✅ Confirm to apply these settings"""
            
            restore_buttons = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✏️ Edit", callback_data="edit_backup"),
                    InlineKeyboardButton("✅ Confirm", callback_data="confirm_backup")
                ],
                [InlineKeyboardButton("Cancel", callback_data="menu_main")]
            ])
            
            await callback.message.edit_text(text_msg, reply_markup=restore_buttons)
            await callback.answer()
            
        except Exception as e:
            print(f"❌ Restore error: {e}")
            await callback.answer(f"❌ Error: {e}", show_alert=True)
    
    @app.on_callback_query(filters.regex("^edit_backup$") & owner_callback_filter)
    async def edit_backup_callback(client: Client, callback: CallbackQuery):
        """Prompt user to paste edited JSON"""
        user_id = callback.from_user.id
        if user_id not in user_data:
            user_data[user_id] = {}
        
        user_data[user_id]['waiting_for'] = 'backup_json_edit'
        
        await callback.message.edit_text(
            "✏️ **Edit Backup Settings**\n\n"
            "Paste the edited JSON settings below:\n\n"
            "(Start with `{` for JSON text)",
            reply_markup=get_cancel_button()
        )
        await callback.answer()
    
    @app.on_callback_query(filters.regex("^confirm_backup$") & owner_callback_filter)
    async def confirm_backup_callback(client: Client, callback: CallbackQuery):
        """Apply backup settings to bot"""
        try:
            user_id = callback.from_user.id
            
            if user_id not in user_data or 'backup_data' not in user_data[user_id]:
                await callback.answer("❌ No backup data found", show_alert=True)
                return
            
            await callback.message.edit_text("⏳ **Applying settings...**")
            
            backup_data = user_data[user_id]['backup_data']
            
            # Apply settings to Config
            Config.SOURCE_CHANNEL_IDS = backup_data.get("source_channels", [])
            Config.DESTINATION_CHANNEL_IDS = backup_data.get("destination_channels", [])
            Config.WHITELIST_WORDS = backup_data.get("whitelist_words", [])
            Config.BLACKLIST_WORDS = backup_data.get("blacklist_words", [])
            Config.REMOVED_WORDS = backup_data.get("removed_words", [])
            Config.FILE_PREFIX = backup_data.get("file_prefix", "")
            Config.FILE_SUFFIX = backup_data.get("file_suffix", "")
            Config.REMOVE_USERNAME = backup_data.get("remove_username", False)
            Config.CUSTOM_CAPTION = backup_data.get("custom_caption", "")
            Config.START_LINK = backup_data.get("start_link")
            Config.END_LINK = backup_data.get("end_link")
            Config.PROCESS_ABOVE_2GB = backup_data.get("process_above_2gb", False)
            
            # Save to current settings in MongoDB
            await save_settings(backup_data)
            
            user_data[user_id]['waiting_for'] = None
            
            # Check if start/end links are restored and ask for confirmation
            if Config.START_LINK and Config.END_LINK:
                range_msg = (
                    "✅ **Settings Restored Successfully!**\n\n"
                    f"📁 Source Channels: {len(Config.SOURCE_CHANNEL_IDS)}\n"
                    f"📤 Dest Channels: {len(Config.DESTINATION_CHANNEL_IDS)}\n"
                    f"✔️ Whitelist: {len(Config.WHITELIST_WORDS)} words\n"
                    f"❌ Blacklist: {len(Config.BLACKLIST_WORDS)} words\n"
                    f"✂️ Remove Words: {len(Config.REMOVED_WORDS)} words\n"
                    f"📝 Prefix: {Config.FILE_PREFIX if Config.FILE_PREFIX else 'None'}\n"
                    f"📝 Suffix: {Config.FILE_SUFFIX if Config.FILE_SUFFIX else 'None'}\n"
                    f"📋 **Message Range Restored:**\n"
                    f"Start: {Config.START_LINK}\n"
                    f"End: {Config.END_LINK}\n\n"
                    "✅ **Is this message range OK?**"
                )
                range_buttons = InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ Yes, OK", callback_data="range_confirmed"),
                     InlineKeyboardButton("❌ No, Change", callback_data="menu_setrange")]
                ])
                await callback.message.edit_text(range_msg, reply_markup=range_buttons)
            else:
                success_msg = (
                    "✅ **Settings Restored Successfully!**\n\n"
                    f"📁 Source Channels: {len(Config.SOURCE_CHANNEL_IDS)}\n"
                    f"📤 Dest Channels: {len(Config.DESTINATION_CHANNEL_IDS)}\n"
                    f"✔️ Whitelist: {len(Config.WHITELIST_WORDS)} words\n"
                    f"❌ Blacklist: {len(Config.BLACKLIST_WORDS)} words\n"
                    f"✂️ Remove Words: {len(Config.REMOVED_WORDS)} words\n"
                    f"📝 Prefix: {Config.FILE_PREFIX if Config.FILE_PREFIX else 'None'}\n"
                    f"📝 Suffix: {Config.FILE_SUFFIX if Config.FILE_SUFFIX else 'None'}\n"
                    f"🎬 Premium: {'✅ ON' if Config.PROCESS_ABOVE_2GB else '❌ OFF'}"
                )
                await callback.message.edit_text(success_msg, reply_markup=get_settings_menu())
            await callback.answer("✅ Settings applied!")
            
        except Exception as e:
            print(f"❌ Confirm error: {e}")
            await callback.answer(f"❌ Error: {e}", show_alert=True)
    
    @app.on_message(filters.text & filters.private & owner_filter)
    async def handle_backup_json_edit(client: Client, message: Message):
        """Handle edited JSON from user"""
        user_id = message.from_user.id
        
        if user_id not in user_data or user_data[user_id].get('waiting_for') != 'backup_json_edit':
            return
        
        try:
            text = message.text.strip()
            if not text.startswith('{'):
                return
            
            # Parse edited JSON
            edited_backup = json.loads(text)
            
            # Store edited backup
            user_data[user_id]['backup_data'] = edited_backup
            user_data[user_id]['waiting_for'] = 'restore_confirm'
            
            # Show confirmation with edited settings
            success_msg = (
                "✅ **JSON Parsed Successfully!**\n\n"
                f"📁 Source Channels: {len(edited_backup.get('source_channels', []))}\n"
                f"📤 Dest Channels: {len(edited_backup.get('destination_channels', []))}\n"
                f"✔️ Whitelist: {len(edited_backup.get('whitelist_words', []))} words\n"
                f"❌ Blacklist: {len(edited_backup.get('blacklist_words', []))} words\n\n"
                "Now click ✅ Confirm to apply these edited settings"
            )
            
            confirm_buttons = InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Confirm", callback_data="confirm_backup")],
                [InlineKeyboardButton("Cancel", callback_data="menu_main")]
            ])
            
            await message.reply_text(success_msg, reply_markup=confirm_buttons)
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON parse error: {e}")
            await message.reply_text(f"❌ Invalid JSON: {e}\n\nPlease try again.", reply_markup=get_cancel_button())
            user_data[user_id]['waiting_for'] = None
        except Exception as e:
            print(f"❌ Error: {e}")
            await message.reply_text(f"❌ Error: {e}", reply_markup=get_cancel_button())
            user_data[user_id]['waiting_for'] = None
    
    @app.on_callback_query(filters.regex("^import_settings$") & owner_callback_filter)
    async def import_settings_callback(client: Client, callback: CallbackQuery):
        """Handle import settings button click"""
        user_id = callback.from_user.id
        if user_id not in user_data:
            user_data[user_id] = {}
        user_data[user_id]['waiting_for'] = 'import_file'
        
        await callback.message.edit_text(
            "📥 **Import Settings**\n\n"
            "Choose import method:\n\n"
            "**Option 1:** Send .json file\n"
            "**Option 2:** Paste JSON text directly\n\n"
            "Both methods will load:\n"
            "• Source & Destination Channels\n"
            "• Whitelist & Blacklist\n"
            "• Prefix & Suffix\n"
            "• Premium Mode & Parallel Processing\n"
            "• Custom Caption",
            reply_markup=get_cancel_button()
        )
        await callback.answer()
    
    @app.on_message(filters.document & filters.private & owner_filter)
    async def import_file_handler(client: Client, message: Message):
        """Handle imported settings file - accepts any .json file"""
        user_id = message.from_user.id
        
        # Only process JSON files
        if not message.document.file_name.endswith('.json'):
            return
        
        # Only process if waiting for import or if it's bot_settings.json
        if user_id not in user_data or (user_data[user_id].get('waiting_for') != 'import_file' and message.document.file_name != 'bot_settings.json'):
            print(f"[IMPORT] File rejected - not in import mode or wrong filename")
            return
        
        try:
            print(f"[IMPORT] User {user_id} uploading file: {message.document.file_name}")
            
            # Show loading message
            loading_msg = await message.reply_text("⏳ **Downloading file...**")
            
            # Download file - use downloads folder with unique name
            os.makedirs("downloads", exist_ok=True)
            file_path = await client.download_media(message, file_name=f"downloads/{message.document.file_name}")
            print(f"[IMPORT] File downloaded to: {file_path}")
            
            # Show applying settings message
            await loading_msg.edit_text("⏳ **Applying settings...**")
            await asyncio.sleep(0.5)
            
            # Read settings file
            print(f"[IMPORT] Reading settings from: {file_path}")
            with open(file_path, 'r') as f:
                settings_data = json.load(f)
            print(f"[IMPORT] Settings loaded: {list(settings_data.keys())}")
            
            # Prepare settings dict for storage
            new_settings = {
                "source_channels": settings_data.get("source_channels", []),
                "destination_channels": settings_data.get("destination_channels", []),
                "whitelist_words": settings_data.get("whitelist_words", []),
                "blacklist_words": settings_data.get("blacklist_words", []),
                "file_prefix": settings_data.get("file_prefix", ""),
                "file_suffix": settings_data.get("file_suffix", ""),
                "remove_username": settings_data.get("remove_username", False),
                "custom_caption": settings_data.get("custom_caption", ""),
                "start_link": settings_data.get("start_link"),
                "end_link": settings_data.get("end_link"),
                "process_above_2gb": settings_data.get("process_above_2gb", False),
            }
            
            print(f"[IMPORT] Saving to storage...")
            from bot.database import save_settings
            await save_settings(new_settings)
            
            # Apply settings from JSON to Config object
            Config.SOURCE_CHANNEL_IDS = new_settings["source_channels"]
            Config.DESTINATION_CHANNEL_IDS = new_settings["destination_channels"]
            Config.WHITELIST_WORDS = new_settings["whitelist_words"]
            Config.BLACKLIST_WORDS = new_settings["blacklist_words"]
            Config.FILE_PREFIX = new_settings["file_prefix"]
            Config.FILE_SUFFIX = new_settings["file_suffix"]
            Config.REMOVE_USERNAME = new_settings["remove_username"]
            Config.CUSTOM_CAPTION = new_settings["custom_caption"]
            Config.START_LINK = new_settings["start_link"]
            Config.END_LINK = new_settings["end_link"]
            Config.PROCESS_ABOVE_2GB = new_settings["process_above_2gb"]
            
            print(f"[IMPORT] Settings updated in Config and storage")
            
            # Clean up flag
            if user_id in user_data:
                user_data[user_id]['waiting_for'] = None
            
            # Delete file
            try:
                os.remove(file_path)
                print(f"[IMPORT] File deleted: {file_path}")
            except Exception as cleanup_err:
                print(f"[IMPORT] Cleanup error: {cleanup_err}")
            
            # Show success message with updated settings
            success_text = (
                "✅ **Settings Updated Successfully!**\n\n"
                f"📁 Source Channels: {len(Config.SOURCE_CHANNEL_IDS)} configured\n"
                f"📤 Dest Channels: {len(Config.DESTINATION_CHANNEL_IDS)} configured\n"
                f"✔️ Whitelist: {len(Config.WHITELIST_WORDS)} words\n"
                f"❌ Blacklist: {len(Config.BLACKLIST_WORDS)} words\n"
                f"📝 Prefix: {Config.FILE_PREFIX if Config.FILE_PREFIX else 'None'}\n"
                f"📝 Suffix: {Config.FILE_SUFFIX if Config.FILE_SUFFIX else 'None'}\n"
                f"🎬 Premium Mode: {'✅ ON' if Config.PROCESS_ABOVE_2GB else '❌ OFF'}"
            )
            
            print(f"[IMPORT] Sending success message")
            await loading_msg.edit_text(success_text, reply_markup=get_settings_menu())
            print(f"[IMPORT] Import completed successfully!")
            
        except json.JSONDecodeError as e:
            print(f"[IMPORT] JSON decode error: {e}")
            await message.reply_text(f"❌ Invalid JSON file: {e}", reply_markup=get_settings_menu())
        except Exception as e:
            print(f"[IMPORT] Error: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            await message.reply_text(f"❌ Error importing settings: {e}", reply_markup=get_settings_menu())
    
    @app.on_message(filters.text & filters.private & owner_filter)
    async def import_text_handler(client: Client, message: Message):
        """Handle JSON text import - paste JSON directly"""
        user_id = message.from_user.id
        
        # Only process if waiting for import
        if user_id not in user_data or user_data[user_id].get('waiting_for') != 'import_file':
            return
        
        try:
            # Check if message contains JSON
            text = message.text.strip()
            if not text.startswith('{'):
                return
            
            print(f"[IMPORT-TEXT] User {user_id} sending JSON text")
            
            # Show loading message
            loading_msg = await message.reply_text("⏳ **Parsing JSON text...**")
            
            # Parse JSON text
            settings_data = json.loads(text)
            print(f"[IMPORT-TEXT] JSON parsed: {list(settings_data.keys())}")
            
            # Show applying settings message
            await loading_msg.edit_text("⏳ **Applying settings...**")
            await asyncio.sleep(0.5)
            
            # Prepare settings dict for storage
            new_settings = {
                "source_channels": settings_data.get("source_channels", []),
                "destination_channels": settings_data.get("destination_channels", []),
                "whitelist_words": settings_data.get("whitelist_words", []),
                "blacklist_words": settings_data.get("blacklist_words", []),
                "file_prefix": settings_data.get("file_prefix", ""),
                "file_suffix": settings_data.get("file_suffix", ""),
                "remove_username": settings_data.get("remove_username", False),
                "custom_caption": settings_data.get("custom_caption", ""),
                "start_link": settings_data.get("start_link"),
                "end_link": settings_data.get("end_link"),
                "process_above_2gb": settings_data.get("process_above_2gb", False),
            }
            
            print(f"[IMPORT-TEXT] Saving to storage...")
            from bot.database import save_settings
            await save_settings(new_settings)
            
            # Apply settings from JSON to Config object
            Config.SOURCE_CHANNEL_IDS = new_settings["source_channels"]
            Config.DESTINATION_CHANNEL_IDS = new_settings["destination_channels"]
            Config.WHITELIST_WORDS = new_settings["whitelist_words"]
            Config.BLACKLIST_WORDS = new_settings["blacklist_words"]
            Config.FILE_PREFIX = new_settings["file_prefix"]
            Config.FILE_SUFFIX = new_settings["file_suffix"]
            Config.REMOVE_USERNAME = new_settings["remove_username"]
            Config.CUSTOM_CAPTION = new_settings["custom_caption"]
            Config.START_LINK = new_settings["start_link"]
            Config.END_LINK = new_settings["end_link"]
            Config.PROCESS_ABOVE_2GB = new_settings["process_above_2gb"]
            
            print(f"[IMPORT-TEXT] Settings updated in Config and storage")
            
            # Clean up flag
            user_data[user_id]['waiting_for'] = None
            
            # Show success message with updated settings
            success_text = (
                "✅ **Settings Updated Successfully!**\n\n"
                f"📁 Source Channels: {len(Config.SOURCE_CHANNEL_IDS)} configured\n"
                f"📤 Dest Channels: {len(Config.DESTINATION_CHANNEL_IDS)} configured\n"
                f"✔️ Whitelist: {len(Config.WHITELIST_WORDS)} words\n"
                f"❌ Blacklist: {len(Config.BLACKLIST_WORDS)} words\n"
                f"📝 Prefix: {Config.FILE_PREFIX if Config.FILE_PREFIX else 'None'}\n"
                f"📝 Suffix: {Config.FILE_SUFFIX if Config.FILE_SUFFIX else 'None'}\n"
                f"🎬 Premium Mode: {'✅ ON' if Config.PROCESS_ABOVE_2GB else '❌ OFF'}"
            )
            
            print(f"[IMPORT-TEXT] Import completed successfully!")
            await loading_msg.edit_text(success_text, reply_markup=get_settings_menu())
            
        except json.JSONDecodeError as e:
            print(f"[IMPORT-TEXT] JSON decode error: {e}")
            await message.reply_text(f"❌ Invalid JSON format: {e}", reply_markup=get_settings_menu())
            user_data[user_id]['waiting_for'] = None
        except Exception as e:
            print(f"[IMPORT-TEXT] Error: {type(e).__name__}: {e}")
            await message.reply_text(f"❌ Error importing JSON: {e}", reply_markup=get_settings_menu())
            user_data[user_id]['waiting_for'] = None

    return app
