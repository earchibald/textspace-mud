# Railway Development Environment Setup

This document describes how to set up and deploy to a development Railway environment.

## Architecture

```
Local Development (devcontainer)
    ↓
GitHub develop branch
    ↓
Railway Development Environment
    ↓
Testing & Validation
    ↓
GitHub main branch (PR)
    ↓
Railway Production Environment
```

## Prerequisites

1. Railway CLI installed: `npm install -g @railway/cli`
2. Railway account with project access
3. GitHub with SSH keys configured

## Setting Up Development Environment in Railway

### Step 1: Create Development Railway Project

```bash
# Link to the development environment
railway link

# This will prompt you to select or create a project
# Create a new project named "textspace-mud-dev"
```

### Step 2: Configure Environment Variables

In Railway Dashboard for dev project:
```
PORT=8080
RAILWAY_ENVIRONMENT_NAME=development
```

### Step 3: Deploy to Development

```bash
# From the workspace root with .railway/config.json configured for dev
railway up
```

## Development Workflow

### Local Development
```bash
# 1. Start in devcontainer
# 2. Make code changes
# 3. Test locally
python3 server_web_only.py

# 4. Verify functionality works
# Open browser: http://localhost:8080
```

### Push to Develop Branch
```bash
# 1. Commit changes
git add .
git commit -m "feat: description of feature"

# 2. Push to develop branch (trigger auto-deploy if configured)
git push origin develop
```

### Deploy to Development Railway
```bash
# Option A: Manual deployment
cd /workspaces/006-mats
railway up --service textspace-mud --environment development

# Option B: Use provided task
# In VS Code: Terminal > Run Task > Deploy to Dev Railway

# Check logs
railway logs --tail 20
```

### Validate in Development
```bash
# Get dev environment URL from Railway dashboard
# or use:
railway open

# Test functionality:
curl https://[dev-url]/api/status | python3 -m json.tool

# Run integration tests against dev if available
```

### Promote to Production
```bash
# 1. Create pull request from develop to main
git push origin develop
# Create PR on GitHub

# 2. After review and approval, merge to main
# GitHub can be configured for auto-deploy, or manually:
railway link  # Switch to production project
railway up
```

## VS Code Tasks

Add these to `.vscode/tasks.json` for one-click deployment:

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Deploy to Dev Railway",
      "type": "shell",
      "command": "railway up --service textspace-mud --environment development",
      "problemMatcher": [],
      "group": {
        "kind": "build",
        "isDefault": false
      }
    },
    {
      "label": "Deploy to Prod Railway",
      "type": "shell",
      "command": "railway up --service textspace-mud --environment production",
      "problemMatcher": [],
      "group": {
        "kind": "build",
        "isDefault": false
      }
    },
    {
      "label": "Railway Logs (Dev)",
      "type": "shell",
      "command": "railway logs --tail 50 --environment development",
      "problemMatcher": []
    },
    {
      "label": "Railway Logs (Prod)",
      "type": "shell",
      "command": "railway logs --tail 50 --environment production",
      "problemMatcher": []
    }
  ]
}
```

## Environment-Specific Configuration

The application detects Railway environment via `RAILWAY_ENVIRONMENT_NAME`:

```bash
# In start_railway.sh
if [ "$RAILWAY_ENVIRONMENT_NAME" = "production" ]; then
    echo "Running in production mode"
elif [ "$RAILWAY_ENVIRONMENT_NAME" = "development" ]; then
    echo "Running in development mode"
fi
```

## Monitoring & Logs

```bash
# Development logs
railway logs --tail 20 --environment development

# Production logs  
railway logs --tail 20 --environment production

# Real-time logs
railway logs --tail 0 --environment development
```

## Troubleshooting

### Deployment fails
1. Check Railway logs: `railway logs --tail 100`
2. Verify Dockerfile builds locally: `docker build .`
3. Check railway.json syntax

### Environment variables not updating
1. Redeploy: `railway redeploy`
2. Restart service in Railway dashboard

### Port conflicts
- Ensure PORT env var is set (defaults to 8080)
- Local dev: use 8080
- Dev Railway: Railway assigns automatically
- Prod Railway: Railway assigns automatically

## Version Management

Development and production track versions independently in the application:

```python
# In server_web_only.py
VERSION = "2.x.x"  # Automatically updated per deployment

# Each Railway environment maintains its own version
# Check with: curl https://[url]/api/status
```

## Quick Reference

| Task | Command |
|------|---------|
| Switch to dev | `railway link` (select dev project) |
| Deploy dev | `railway up` |
| Deploy prod | `railway link` (switch to prod), then `railway up` |
| View logs | `railway logs --tail 50` |
| Health check | `curl https://[url]/api/status` |
| Open dashboard | `railway open` |

