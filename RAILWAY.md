# Railway Deployment Guide

## Quick Deploy Steps

1. **Push to GitHub** (if not already done):
   ```bash
   git add -A
   git commit -m "Add Railway deployment configuration"
   git push origin main
   ```

2. **Create Railway Project**:
   - Go to [railway.app](https://railway.app)
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your textspace repository

3. **Configure Environment Variables**:
   In Railway dashboard, go to Variables tab and add:
   ```
   SECRET_KEY=your-random-secret-key-here
   USE_DATABASE=true
   DATABASE_PATH=/app/data/textspace.db
   ```

4. **Add Persistent Volume**:
   - Go to Settings → Volumes
   - Add volume: `/app/data` (for SQLite database)

5. **Deploy**:
   - Railway will automatically build and deploy
   - Get your app URL from the dashboard

## Environment Variables

Required variables for Railway:
- `SECRET_KEY`: Random string for security
- `USE_DATABASE`: Set to `true` for production
- `DATABASE_PATH`: `/app/data/textspace.db`

Optional variables:
- `HOST`: `0.0.0.0` (default)
- `TCP_PORT`: `8888` (default)
- `WEB_PORT`: `5000` (default)

## Accessing Your App

After deployment:
- **Web Interface**: `https://your-app.railway.app`
- **TCP Connection**: Use Railway's TCP proxy or ngrok for external access

## Database Migration

To migrate existing data:
1. Deploy the app first
2. Use the migration tool via Railway's console
3. Upload your existing data files

## Monitoring

Railway provides:
- Automatic logs
- Metrics dashboard
- Health checks
- Automatic restarts

## Scaling

Railway automatically handles:
- Resource scaling
- SSL certificates
- Domain management
- Backups (with persistent volumes)

## Cost

- Free tier: Limited hours
- Hobby plan: $5/month for always-on
- Includes: Hosting, database storage, SSL, monitoring
