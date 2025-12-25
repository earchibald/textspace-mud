# TextSpace Deployment Process

## Current Deployment Architecture

**Platform**: Railway (https://railway.app)  
**Repository**: GitHub (earchibald/textspace-mud)  
**CI/CD**: GitHub Actions + Multi-Environment Railway Deployment  
**Server**: Python Flask + SocketIO  
**Environments**: Development → Production Workflow

### Branch Strategy
```
feature/xxx → develop (Dev Railway) → main (Prod Railway)
```

## Development Environment Workflow

### Dev to Production Pipeline

**Step 1: Local Development (devcontainer)**
```bash
git checkout develop
git pull origin develop

# Create feature branch
git checkout -b feature/my-feature

# Make changes and test locally
python3 server_web_only.py
# Test functionality...

# Commit changes
git add .
git commit -m "feat: description of feature"
```

**Step 2: Deploy to Development Railway**
```bash
# Push feature branch
git push origin feature/my-feature

# Create PR to develop on GitHub
# After approval, merge to develop

# Automatic: develop branch deploys to Railway Dev environment
# Monitor: railway logs --environment development

# Or manually deploy:
railway up --environment development
```

**Step 3: Test in Development Railway**
```bash
# Get dev environment URL from Railway dashboard
# Test functionality at https://[dev-url]

# Verify health check
curl -s https://[dev-url]/api/status | python3 -m json.tool
```

**Step 4: Promote to Production**
```bash
# When develop is stable and tested, create PR to main
git fetch origin
git checkout main
git merge develop  # or use GitHub PR interface

# Automatic: main branch deploys to Railway Production environment
# Or manually:
railway up --environment production

# Verify: curl -s https://[prod-url]/api/status
```

## Detailed Deployment Steps

### 1. Local Development & Testing
```bash
# Test locally for syntax errors
python3 -m py_compile server_web_only.py

# Run local server for testing
python3 server_web_only.py
```

### 2. Version Management (Optional)
```bash
# Update VERSION constant in server_web_only.py
# Follow semver: MAJOR.MINOR.PATCH
VERSION = "2.5.2"
```

### 3. Git Workflow
```bash
# Branch from develop (not main)
git checkout -b feature/description

# Make changes and test
# ... code changes ...

# Commit with semantic message
git add .
git commit -m "feat: feature description"
git commit -m "fix: bug description"
git commit -m "refactor: code organization"

# Push to feature branch
git push -u origin feature/description
```

### 4. Create Pull Request
- On GitHub, create PR from `feature/xxx` to `develop`
- Fill out PR template with description and testing evidence
- Wait for code review and CI checks to pass
- Merge to develop after approval

### 5. Development Railway Deployment
```bash
# After merge to develop, automatically deploys to Dev Railway
# Monitor the deployment:
railway logs --environment development --tail 50

# Verify it's running:
# Check Railway dashboard for dev project
# Or manually: railway open --environment development
```

### 6. Development Testing & Validation
```bash
# Test in Dev Railway environment
# Get URL from Railway dashboard or: railway open --environment development

# Validate functionality
curl -s "https://[dev-url]/api/status" | python3 -m json.tool

# Check server logs if issues
railway logs --environment development --tail 100
```

### 7. Promote to Production
```bash
# When develop is stable, create PR from develop to main
# On GitHub: develop → main

# After approval and merge, automatically deploys to Production
# Verify: curl -s "https://[prod-url]/api/status"
```

### 8. Production Validation (60 Second Wait)
```bash
# Wait 60 seconds for Railway to cycle versions
sleep 60

# Check production server status
curl -s "https://exciting-liberation-production.up.railway.app/api/status" | python3 -m json.tool

# Monitor logs
railway logs --environment production --tail 50
```

## Key Insights from Experience

### Railway Deployment Behavior
- **Branch-based deployment**: develop branch → Dev Railway, main branch → Prod Railway
- **Manual `railway up` still supported**: For emergency deployments or manual control
- **Version bumps help**: Changing VERSION constant forces proper rebuild
- **60 second cycle time**: Railway needs 60 seconds to cycle versions

### Common Issues & Solutions
- **Dev deployment not updating**: Force redeploy with `railway redeploy --environment development`
- **Prod deployment stuck**: Check GitHub CI for syntax errors, then manually: `railway up --environment production`
- **Server not responding**: Check Railway logs with `railway logs --tail 20 --environment [dev|production]`
- **Wrong environment deployed**: Verify RAILWAY_ENVIRONMENT_NAME variable in Railway dashboard

### Version History Tracking
- Use semantic versioning consistently: MAJOR.MINOR.PATCH
- Tag releases: `git tag v2.7.4 && git push origin --tags`
- Document changes in commit messages
- Each environment tracks its own version via `/api/status`

## Monitoring & Rollback

### Health Checks
- `/api/status` endpoint shows version and basic health
- Development: `curl https://[dev-url]/api/status`
- Production: `curl https://exciting-liberation-production.up.railway.app/api/status`
- WebSocket connection test via web interface
- Server logs via `railway logs --environment [dev|production]`

### Rollback Process

**If develop has issues:**
```bash
git checkout develop
git log --oneline -5  # Find previous good commit
git revert <commit-hash>
git push origin develop
# Automatically redeploys Dev Railway with the revert
```

**If production has issues:**
```bash
git checkout main
git log --oneline -5  # Find previous good commit
git revert <commit-hash>
git push origin main
# Automatically redeploys Production Railway

# Or force redeploy previous version:
railway redeploy --environment production
```

## Multi-Environment Variables

### Development Environment (.railway/config-dev.json)
```json
{
  "PORT": "8080",
  "RAILWAY_ENVIRONMENT_NAME": "development"
}
```

### Production Environment (railway.json)
```json
{
  "PORT": "8080",
  "RAILWAY_ENVIRONMENT_NAME": "production"
}
```

## Branching & Deployment Relationship

| Branch | Environment | Auto-Deploy | Railway URL | Status Endpoint |
|--------|-------------|-------------|------------|-----------------|
| develop | Development | On merge | https://[dev-url] | /api/status |
| main | Production | On merge | https://exciting-liberation-production.up.railway.app | /api/status |
| feature/* | Local | Manual | http://localhost:8080 | /api/status |

## Environment Detection in Code

The application automatically detects its environment:

```python
# In server_web_only.py or config
import os

env = os.getenv('RAILWAY_ENVIRONMENT_NAME', 'local')
if env == 'production':
    # Production-specific setup
    pass
elif env == 'development':
    # Development-specific setup
    pass
else:
    # Local development
    pass
```

## VS Code Deployment Tasks

Quick deployment commands available in VS Code:

```bash
Terminal > Run Task:
- "Run Server Locally" - Start dev server
- "Deploy to Dev Railway" - Deploy to development environment
- "Deploy to Production Railway" - Deploy to production environment
- "View Dev Railway Logs" - Monitor dev deployment
- "View Production Railway Logs" - Monitor prod deployment
```

## Future Improvements
- Automated testing in Dev Railway before promotion to Prod
- Pre-deployment validation and health checks
- Automated rollback on deployment failure
- Blue-green deployment for zero downtime updates
- Performance monitoring and alerts
