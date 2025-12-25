# Railway Development Environment - Quick Start

## What's Been Implemented

✅ **Develop Branch Created**
- New `develop` branch for ongoing development
- All feature development goes to develop first
- **Status**: Branch created but NOT YET connected to Railway Dev

⏳ **Multi-Environment Railway Setup** (Pending Connection)
- `railway-dev.json` - Configuration for development environment
- Separate environment variables for dev vs production
- Environment detection in startup script
- **Status**: Configuration ready, needs to be connected via Railway Dashboard

✅ **VS Code Deployment Tasks**
- `.vscode/tasks.json` with 8 deployment and monitoring tasks
- One-click deployment from VS Code terminal
- Separate tasks for dev and prod environments

✅ **Documentation**
- `/BRANCHING_STRATEGY.md` - Complete branch workflow guide
- `.devcontainer/railway-dev-setup.md` - Development environment setup
- Updated deployment process in `_bmad/_config/deployment-process.md`

## ⚠️ IMPORTANT: Connection Required

**The develop branch is NOT YET connected to the Railway dev environment.**

To complete the setup, you must:
1. Go to Railway Dashboard
2. Select your `textspace-mud` development environment  
3. Change Git deployment from `main` to `develop`
4. Set environment variables

See [.devcontainer/RAILWAY_DEVELOP_BRANCH_SETUP.md](.devcontainer/RAILWAY_DEVELOP_BRANCH_SETUP.md) for detailed instructions.

## Getting Started

### ⚠️ FIRST: Connect Develop Branch to Railway Dev (REQUIRED STEP)

Before using the workflow below, you must connect the develop branch to Railway's development environment:

**Quick Steps:**
1. Go to https://railway.app/dashboard
2. Select `textspace-mud` project → `development` environment
3. Click the `textspace-mud` service
4. Click **Settings** → **Git** → Change "Deploy from branch" to **develop**
5. Go to **Variables** tab and add:
   - `PORT=8080`
   - `RAILWAY_ENVIRONMENT_NAME=development`
6. Save changes

[Detailed guide: .devcontainer/RAILWAY_DEVELOP_BRANCH_SETUP.md](.devcontainer/RAILWAY_DEVELOP_BRANCH_SETUP.md)

### 1. Understand the Workflow
Read: `BRANCHING_STRATEGY.md`

```
Local Dev (devcontainer)
    ↓
git feature/xxx → develop
    ↓
Auto-deploy to Railway Dev (once configured above)
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
- `.devcontainer/RAILWAY_DEVELOP_BRANCH_SETUP.md` - **Connect develop branch to dev environment**
- `_bmad/_config/deployment-process.md` - Deployment process documentation
- `.vscode/tasks.json` - VS Code deployment and monitoring tasks
- `railway-dev.json` - Development Railway configuration
- `railway.json` - Production Railway configuration

## Next Steps

### 1. **⚠️ REQUIRED: Connect Develop Branch to Development Environment** 
   
   **This must be done in Railway Dashboard before development can proceed.**
   
   - Read: `.devcontainer/RAILWAY_DEVELOP_BRANCH_SETUP.md` for detailed instructions
   - **Simplest method**: Use Railway Dashboard UI (no CLI needed)
     1. Go to https://railway.app/dashboard
     2. Select `textspace-mud` project → `development` environment
     3. Click `textspace-mud` service
     4. Click **Settings** → **Git** → Change branch to **develop**
     5. Click **Variables** → Add `PORT=8080` and `RAILWAY_ENVIRONMENT_NAME=development`
     6. Save and wait for deploy
   
   - **Alternative**: Use Railway CLI (requires Node.js)
     ```bash
     npm install -g @railway/cli
     railway link
     railway variables set PORT 8080
     railway variables set RAILWAY_ENVIRONMENT_NAME development
     railway up
     ```

### 2. **Start Development** (After step 1 is complete)
   - Create feature branch from develop
   - Make changes
   - Merge to develop
   - Watch auto-deployment to Dev Railway

3. **Promote When Ready**
   - Create PR from develop to main
   - After approval, merge to main
   - Verify in Production Railway

## Support

For detailed information:
- Branch workflow: See `BRANCHING_STRATEGY.md`
- Railway setup: See `.devcontainer/railway-dev-setup.md`
- Deployment process: See `_bmad/_config/deployment-process.md`
