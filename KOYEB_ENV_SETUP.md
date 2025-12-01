# Koyeb Environment Variables Setup

## Required Environment Variables

Add these to your Koyeb service secrets:

```
TELEGRAM_API=25713073
TELEGRAM_HASH=65a23aaa7a97f42475de52ed240af2f3
BOT_TOKEN=8155671926:AAFm2V87F76qj_gEm_gJFD-mknWHHzqGxzo
OWNER_ID=6927710017
DATABASE_URL=mongodb+srv://leechbot:leechbot01@cluster0.vxfsb.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0
```

## Steps to Add in Koyeb:

1. Go to Koyeb Dashboard
2. Select your **autorenamer-bot** service
3. Click **Settings** → **Secrets** (or **Environment**)
4. Add each variable above
5. Click **Deploy** or **Redeploy**
6. Check logs to verify bot starts successfully

## Verification

Bot should start with messages:
```
✅ MongoDB connected successfully
==================================================
Channel File Processor Bot
==================================================
Configuration status:
  - API: ✅ OK
  - Bot Token: ✅ OK
  - MongoDB: ✅ Connected
```

## Notes

- `TELEGRAM_API` is your Telegram API ID
- `TELEGRAM_HASH` is your Telegram API Hash
- `BOT_TOKEN` is from @BotFather
- `OWNER_ID` is your Telegram user ID
- `DATABASE_URL` is your MongoDB connection string

All credentials are now properly referenced in the code!
