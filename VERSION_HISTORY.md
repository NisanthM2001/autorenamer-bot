# Version History

## Version 01.01.01 - STABLE RELEASE (Current)
**Date:** December 1, 2025
**Status:** ✅ PRODUCTION READY - All features tested and stable

### Features in this Version:
✅ Sequential file processing (one file at a time)
✅ Real-time progress UI updates every 3 seconds
✅ Dynamic file counting (total, to process, premium, skipped)
✅ Current file index tracking (1/10, 2/10, etc)
✅ Completed files counter (increments only after success)
✅ Queue display with 5+ pending files
✅ Skip indicators (✗ Skip, ⭐ Premium, ✓ Process)
✅ Language & subtitle extraction for captions
✅ Remove words with append mode + clear all button
✅ Whitelist/Blacklist filtering
✅ Smart filename renaming
✅ Prefix/Suffix support
✅ Multi-channel upload
✅ Custom thumbnails
✅ Message range processing
✅ Telegram Premium support (>2GB files)
✅ Cancel All button
✅ PostgreSQL persistent storage
✅ Export/Import settings as JSON
✅ Production VM deployment configured

### UI Layout (This Version):
```
📥 DOWNLOADING 1/10

📄 current_file.mkv

████████░░ 65%
💾 450MB / 680MB
🚀 2.3MB/s

━━━━━━━━━━━━━━━━━━
📋 QUEUE (8+):
  1. ✓ file1.mkv
  2. ⭐ premium_file.mkv
  3. ✗ video.mkv (Skip - Blacklist)
  4. ✓ series.mkv
  5. ⭐ hd_movie.mkv
  +3 more...

━━━━━━━━━━━━━━━━━━
📈 PROGRESS:
  ✅ Processed: 1
  ⏳ Currently: Downloading
  📌 Remaining: 8

📊 FILE COUNTS:
  📥 Total Found: 15
  ✓ To Process: 10
  ⭐ Premium (>2GB): 3
  ✗ Skipped: 5
```

### Core Files:
- `main.py` - Bot entry point
- `bot/processor.py` - Sequential processing with real-time UI
- `bot/handlers.py` - Command handlers and UI interactions
- `bot/database.py` - PostgreSQL storage
- `bot/filters.py` - File filtering logic
- `bot/config.py` - Configuration management
- `bot/client.py` - Pyrogram client setup
- `bot/thumbnail.py` - Thumbnail management

### How to Rollback to 01.01.01:
If any errors occur after this version, you can restore the code to this stable state by:
1. Checking this file to see what was in v01.01.01
2. Reviewing the UI layout documented above
3. Reference the feature list to compare what changed

### Notes:
- All processed files increment ONLY after successful download + upload
- Current file index shows which file is being processed (updates at START)
- File counts calculated from full range scan before processing starts
- Queue updates every 3 seconds during both download and upload phases
- Premium detection: files >2GB (2,147,483,648 bytes)
- Remove Words: append mode (send new words to add), Clear All button to empty

---

## Future Versions:
Any new features or changes will be documented above this section.
This version (01.01.01) remains as the stable baseline reference.
