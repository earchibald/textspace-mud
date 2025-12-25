# Railway Development Environment - Quick Start

## What's Been Implemented

✅ **Develop Branch Created**
- New `develop` branch for ongoing development
- All feature development goes to develop first
- develop automatically deploys to Railway Dev environment

✅ **Multi-Environment Railway Setup**
- `railway-dev.json` - Configuration for development environment
- Separate environment variables for dev vs production
- Environment detection in startup script

✅ **VS Code Deployment Tasks**
- `.vscode/tasks.json` with 8 deployment and monitoring tasks
- One-click deployment from VS Code terminal
- Separate tasks for dev and prod environments

✅ **Documentation**
- `/BRANCHING_STRATEGY.md` - Complete branch workflow guide
- `.devcontainer/railway-dev-setup.md` - Development environment setup
- Updated deployment process in `_bmad/_config/deployment-process.md`

## Getting Started

### 1. Understand the Workflow
Read: `BRANCHING_STRATEGY.md`

```
Local Dev (devcontainer)
    ↓
git feature/xxx → develop
    ↓
Auto-deploy to Railway Dev
    ↓
Test & verify in Dev Railway
    ↓
PR develop → main
    ↓
Auto-deploy to Railway Production
```

### 2. Make Code Changes
```bash
# Always start from develop
git checkout develop
git pull origin develop

# Create feature branch
git checkout -b feature/my-feature-name

# Make changes and test locally
python3 server_web_only.py

# Test functionality at http://localhost:8080
```

### 3. Commit and Push
```bash
git add .
git commit -m "feat: description of changes"
git push -u origin feature/my-feature-name
```

### 4. Create Pull Request
- Go to GitHub
- Create PR from `feature/my-feature-name` → `develop`
- Fill out PR description
- Wait for review

### 5. Deploy to Development (Automatic)
- Once merged to develop, Railway Dev environment updates automatically
- Monitor at: `Terminal > Run Task > View Dev Railway Logs`
- Or check Railway dashboard

### 6. Test in Development Railway
```bash
# Get dev URL from Railway dashboard
curl https://[dev-url]/api/status

# Test functionality in the dev environment
```

### 7. Promote to Production (When Ready)
- Create PR: `develop` → `main`
- After approval, merge to main
- Production Railway updates automatically

## VS Code Tasks Reference

Access via: `Terminal` → `Run Task` → Select task

| Task | Purpose |
|------|---------|
| **Run Server Locally** | Start dev server on localhost:8080 |
| **Deploy to Dev Railway** | Manual deploy to dev environment |
| **Deploy to Production Railway** | Manual deploy to production |
| **View Dev Railway Logs** | Monitor dev deployment logs |
| **View Production Railway Logs** | Monitor prod deployment logs |
| **Check Dev Server Status** | Get dev server health status |
| **Install Dependencies** | Run pip install for requirements |
| **Test Python Imports** | Verify all dependencies installed |

## Environment Variables

### Development
```
PORT=8080
RAILWAY_ENVIRONMENT_NAME=development
```

### Production
```
PORT=8080
RAILWAY_ENVIRONMENT_NAME=production
```

## Troubleshooting

**Develop branch not auto-deploying?**
1. Verify merge to develop was successful
2. Check Railway dashboard for errors
3. Force redeploy: `railway redeploy --environment development`

**Want to manually deploy?**
```bash
# Deploy to dev
railway up --environment development

# Deploy to production
railway up --environment production
```

**Check what's deployed?**
```bash
# Dev version
curl https://[dev-url]/api/status | python3 -m json.tool

# Prod version
curl https://exciting-liberation-production.up.railway.app/api/status | python3 -m json.tool
```

## Key Files

- `BRANCHING_STRATEGY.md` - Complete branch strategy and workflow
- `.devcontainer/railway-dev-setup.md` - Dev environment detailed setup
- `_bmad/_config/deployment-process.md` - Deployment process documentation
- `.vscode/tasks.json` - VS Code deployment and monitoring tasks
- `railway-dev.json` - Development Railway configuration
- `railway.json` - Production Railway configuration

## Next Steps

1. **Set up Railway Dev Project** (if not already done)
   - Run: `railway link` and select/create dev project
   - Set environment variables from "Environment Variables" section above

2. **Start Development**
   - Create feature branch
   - Make changes
   - Merge to develop
   - Test in Dev Railway

3. **Promote When Ready**
   - Create PR to main
   - After approval, merge
   - Verify in Production Railway

## Support

For detailed information:
- Branch workflow: See `BRANCHING_STRATEGY.md`
- Railway setup: See `.devcontainer/railway-dev-setup.md`
- Deployment process: See `_bmad/_config/deployment-process.md`
