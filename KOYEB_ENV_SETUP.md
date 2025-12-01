# Koyeb Environment Variables Setup

## MongoDB Connection String

**Current Database:**
```
mongodb+srv://leechpro:leechpro@leechpro2.0731z.mongodb.net/?retryWrites=true&w=majority&appName=LeechPro2
```

## Bot Credentials

```
TELEGRAM_API=25713073
TELEGRAM_HASH=65a23aaa7a97f42475de52ed240af2f3
BOT_TOKEN=8155671926:AAFm2V87F76qj_gEm_gJFD-mknWHHzqGxzo
OWNER_ID=6927710017
DATABASE_URL=mongodb+srv://leechpro:leechpro@leechpro2.0731z.mongodb.net/?retryWrites=true&w=majority&appName=LeechPro2
```

## Steps to Deploy:

1. **Go to Koyeb Dashboard** → **autorenamer-bot** service
2. Click **Settings** → **Environment** or **Secrets**
3. Add/Update these variables
4. Click **Save** and **Redeploy**

## Expected Logs After Redeployment:

```
✅ MongoDB connected successfully
Configuration status:
  - Telegram API: ✅ OK
  - Bot Token: ✅ OK
  - Owner ID: ✅ OK
Starting bot...
```

## Whitelist MongoDB IP

**Important:** If you still get timeout errors, whitelist Koyeb's IP in MongoDB Atlas:

1. Go to **MongoDB Atlas** → **Security** → **Network Access**
2. Click **+ Add IP Address**
3. Choose **Allow Access from Anywhere** (0.0.0.0/0)
4. Click **Confirm**

Your bot will now connect successfully!
