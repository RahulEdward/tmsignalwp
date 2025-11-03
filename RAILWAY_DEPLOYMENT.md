# Railway Deployment Guide for Trading Bridge App

## Prerequisites
- Railway account (https://railway.app)
- GitHub repository connected to Railway

## Deployment Steps

### 1. Create New Railway Project
1. Go to https://railway.app
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose the `tmsignalwp` repository

### 2. Configure Environment Variables
Add these environment variables in Railway dashboard (Settings → Variables):

```
APP_KEY=your_random_secret_key_here_min_32_chars
DATABASE_URL=postgresql://username:password@host:port/dbname
NGROK_ALLOW=FALSE
HOST_SERVER=https://your-app-name.up.railway.app
LOGIN_RATE_LIMIT_MIN=5 per minute
LOGIN_RATE_LIMIT_HOUR=25 per hour
API_RATE_LIMIT=10 per second
PORT=5000
```

### 3. Add PostgreSQL Database (Recommended)
1. In Railway project, click "New"
2. Select "Database" → "PostgreSQL"
3. Railway will auto-create `DATABASE_URL` variable
4. Copy the connection string to your environment variables

**Note:** For SQLite (development), use:
```
DATABASE_URL=sqlite:///db/algo.db
```

### 4. Deploy
1. Railway will automatically detect Python and start building
2. It will use the `Procfile` for deployment
3. Build takes 2-5 minutes
4. Once deployed, you'll get a URL like: `https://your-app-name.up.railway.app`

### 5. Update HOST_SERVER
After deployment, update the `HOST_SERVER` environment variable with your actual Railway URL.

## Important Notes

✅ **Files Added for Railway:**
- `Procfile` - Tells Railway how to start the app
- `railway.json` - Railway configuration
- `requirements.txt` - Includes `eventlet` for SocketIO support

✅ **Database:**
- For production, use PostgreSQL (Railway provides it)
- SQLite works but data is ephemeral on Railway

✅ **WebSocket Support:**
- Uses `eventlet` worker for Flask-SocketIO
- Ensures real-time trading signals work properly

## Testing After Deployment
1. Visit: `https://your-app-name.up.railway.app/api/test`
2. Should return: `{"status": "success", "message": "CORS is working!"}`

## Monitoring
- Check logs: Railway Dashboard → Deployments → View Logs
- Monitor performance in Railway metrics

## Troubleshooting

**Build fails:**
- Check Railway logs for Python/dependency errors
- Verify all environment variables are set

**App crashes on startup:**
- Check if DATABASE_URL is set correctly
- Ensure APP_KEY is set

**WebSocket not working:**
- Verify `eventlet` is in requirements.txt
- Check Procfile uses `--worker-class eventlet`

## Cost
- Railway offers $5 free credit per month
- PostgreSQL database included in hobby plan
- Monitor usage to avoid overages
