# AutoRenamer Bot - Simple Edition

A lightweight Telegram bot that downloads files and uploads them to multiple destinations without database storage.

## Features
- Download files from source channels
- Upload to multiple destination channels
- Smart filename processing (remove words, prefixes, suffixes)
- Session-only settings (no persistence)
- No database required

## Setup

1. Set these credentials in `bot/config.py`:
   - API_ID: 25713073
   - API_HASH: Your API Hash
   - BOT_TOKEN: Your bot token
   - OWNER_ID: Your Telegram user ID

2. Run the bot:
   ```bash
   python main.py
   ```

## Commands

- `/start` - Main menu
- `/help` - Help text
- `/setsource <channel_id>` - Set source channel
- `/setdest <channel_id>` - Set destination channel
- `/process` - Start processing

## Deployment

### Local
```bash
python main.py
```

### Docker
```bash
docker build -t autorenamer .
docker run autorenamer
```

### Koyeb
Push to GitHub and connect Koyeb to auto-deploy.

---

**Note:** Settings are stored in memory only. They reset when the bot restarts. For persistent storage, add a database.
