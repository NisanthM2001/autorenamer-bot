# Koyeb Deployment Guide - AutoRenamer Bot

## Prerequisites
- Koyeb account (https://www.koyeb.com)
- GitHub repository with autorenamer-bot code
- Telegram API credentials (API_ID, API_HASH, BOT_TOKEN, OWNER_ID)
- MongoDB connection string

## Quick Deployment Steps

### 1. Connect GitHub
1. Go to Koyeb Dashboard → "Create Service"
2. Select "GitHub" as source
3. Authorize and select `autorenamer-bot` repository
4. Choose `main` branch

### 2. Configure Service
- **Name**: `autorenamer-bot`
- **Builder**: Docker (auto-detected from Dockerfile)
- **Port**: Not needed (bot is long-running)

### 3. Add Secrets (Environment Variables)
Click "Secrets" and add all values from `bot/config.py`:

```
API_ID=your_api_id
API_HASH=your_api_hash_here
BOT_TOKEN=your_bot_token_here
OWNER_ID=your_owner_id
MONGODB_URL=mongodb+srv://user:pass@cluster.mongodb.net/db
```

### 4. Deploy
Click "Deploy" and wait 2-3 minutes for build to complete.

### 5. Verify
- Check logs in Koyeb Dashboard
- Confirm bot started successfully
- Test bot in Telegram

## Auto-Redeploy
Every git push to `main` triggers automatic redeploy!

## Local Testing

```bash
# Build Docker image
docker build -t autorenamer-bot .

# Run with docker-compose (includes MongoDB)
docker-compose up

# Stop
docker-compose down
```

## Troubleshooting

**Bot not starting:**
- Check environment variables in Koyeb
- Verify MongoDB URL is correct
- Check logs for error messages

**Connection issues:**
- Ensure MongoDB URL is accessible
- Verify all env vars are set
- Check Telegram credentials

For help: https://docs.koyeb.com
