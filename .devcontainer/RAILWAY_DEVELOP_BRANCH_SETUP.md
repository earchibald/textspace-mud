# Connecting Develop Branch to Railway Development Environment

This guide explains how to connect your `develop` branch to the Railway `development` environment.

## Prerequisites

- Railway CLI installed: `npm install -g @railway/cli`
- GitHub repository connected to Railway
- `develop` branch exists in GitHub
- Development environment created in Railway

## Method 1: Using Railway Dashboard (Recommended)

### Step 1: Open Railway Dashboard
1. Go to https://railway.app/dashboard
2. Select your `textspace-mud` project
3. Click on the `development` environment

### Step 2: Configure Git Integration
1. Select the `textspace-mud` service
2. Click **Settings** (gear icon)
3. Scroll down to **Git**
4. Under **Connected Repository**, verify GitHub is connected
5. Under **Deploy from branch**, select `develop` instead of `main`
6. Save changes

### Step 3: Configure Environment Variables
1. Click **Variables** tab in the service
2. Add or verify these variables:
   ```
   PORT=8080
   RAILWAY_ENVIRONMENT_NAME=development
   ```
3. Save changes

### Step 4: Test the Connection
```bash
# Deploy to verify connection
railway up

# Or trigger via GitHub by pushing to develop branch
git push origin develop
```

## Method 2: Using Railway CLI

### Step 1: Install Railway CLI
```bash
# If not already installed
npm install -g @railway/cli
```

### Step 2: Link Your Project
```bash
cd /workspaces/006-mats

# This will prompt you to select a project
# Choose: textspace-mud-dev (or your development project)
railway link
```

### Step 3: Verify Link
```bash
# Show current project
railway project current

# Show current environment
railway environment current
```

### Step 4: Set Environment Variables
```bash
# Set PORT
railway variables set PORT 8080

# Set environment name
railway variables set RAILWAY_ENVIRONMENT_NAME development

# Verify
railway variables list
```

### Step 5: Deploy
```bash
# Deploy develop branch
railway up

# Check status
railway logs --tail 20
```

## Method 3: Using GitHub Actions (Future Enhancement)

Create `.github/workflows/deploy-dev.yml`:

```yaml
name: Deploy to Dev Railway

on:
  push:
    branches:
      - develop

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to Railway (Dev)
        run: |
          npm install -g @railway/cli
          railway deploy --environment development
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
```

## Verification Steps

### 1. Verify Branch Connection
```bash
# In Railway Dashboard:
# Settings > Git > Deploy from branch
# Should show: develop
```

### 2. Verify Environment Variables
```bash
# Check via CLI
railway variables list

# Should show:
# PORT=8080
# RAILWAY_ENVIRONMENT_NAME=development
```

### 3. Verify Deployment
```bash
# Check development URL
# Get from: railway open

# Test health endpoint
curl https://[dev-url]/api/status | python3 -m json.tool

# Check logs
railway logs --tail 50
```

### 4. Test Auto-Deployment
```bash
# Make a test commit to develop
echo "# Test deployment" >> README.md
git add README.md
git commit -m "test: verify develop branch auto-deployment"
git push origin develop

# Monitor in Railway Dashboard or:
railway logs --tail 50 --follow
```

## Troubleshooting

### "Branch not recognized"
- Verify `develop` branch exists in GitHub: `git branch -a`
- Refresh Railway Dashboard (F5)
- Reconnect GitHub integration if needed

### "Deployment stuck"
```bash
# Force redeploy
railway redeploy --environment development

# Or check logs for errors
railway logs --tail 100
```

### "Environment variables not applying"
```bash
# Redeploy after changing variables
railway redeploy --environment development

# Verify variables are set
railway variables list
```

### "Port conflicts"
- Railway automatically assigns ports
- Ensure PORT env var is set (should be 8080)
- Check for other services using port 8080

## Deployment Flow

Once configured:

```
1. Developer pushes to develop branch
   git push origin develop

2. GitHub webhook triggers Railway

3. Railway pulls develop branch

4. Railway builds Docker image using Dockerfile

5. Railway runs start_railway.sh
   - Script detects RAILWAY_ENVIRONMENT_NAME=development
   - Starts server

6. Health check validates at /

7. Service is live at development URL
```

## Quick Reference

| Task | Command |
|------|---------|
| Link to dev project | `railway link` |
| Deploy develop | `railway up` |
| View dev logs | `railway logs --tail 50` |
| Set env variable | `railway variables set KEY value` |
| List variables | `railway variables list` |
| Current project | `railway project current` |
| Current environment | `railway environment current` |
| Open dashboard | `railway open` |
| Redeploy | `railway redeploy` |

## Environment Configuration Files

After connection, these files contain the configuration:

- `.railway/config.json` - Local Railway configuration (auto-generated)
- `railway.json` - Production configuration (committed to repo)
- `railway-dev.json` - Development configuration template

## Next Steps

Once develop branch is connected:

1. ✅ Develop → test locally
2. ✅ Push to develop → auto-deploys to Dev Railway
3. ✅ Test in Dev Railway environment
4. ✅ Create PR develop → main
5. ✅ Merge to main → auto-deploys to Production Railway

## Support

For more information:
- Railway Docs: https://docs.railway.app
- GitHub to Railway: https://docs.railway.app/guides/github
- Environment Variables: https://docs.railway.app/reference/variables
- Deployment: https://docs.railway.app/deploy/deployment

