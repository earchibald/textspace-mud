# TextSpace Deployment Process

## Current Deployment Architecture

**Platform**: Railway (https://railway.app)  
**Repository**: GitHub (earchibald/textspace-mud)  
**CI/CD**: GitHub Actions + Manual Railway Deployment  
**Server**: Python Flask + SocketIO  

## Deployment Steps

### 1. Development & Testing
```bash
# Test locally for syntax errors
python3 -m py_compile server_web_only.py

# Optional: Run local server for testing
python3 server_web_only.py
```

### 2. Version Management
```bash
# Update VERSION constant in server_web_only.py
# Follow semver: MAJOR.MINOR.PATCH
VERSION = "2.5.2"
```

### 3. Git Workflow
```bash
# Stage changes
git add .

# Commit with descriptive message
git commit -m "feat: organized columnar tab completion help v2.5.2"

# Push to main branch
git push origin main
```

### 4. GitHub CI Validation (Parallel)
- GitHub Actions runs automatically on push to main
- Validates Python syntax and basic tests
- **Not required to complete before deployment**
- Check CI results if Railway deployment fails: github.com/earchibald/textspace-mud/actions

### 5. Railway Deployment
```bash
# Deploy to Railway (manual trigger required)
railway up

# Alternative: Force redeploy if needed
railway redeploy
```

### 6. Deployment Validation (60 Second Wait)
```bash
# Wait 60 seconds for Railway to cycle versions
sleep 60

# Check server status
curl -s "https://exciting-liberation-production.up.railway.app/api/status" | python3 -m json.tool

# Or use our MCP server status tool
# Should show new version number
```

## Key Insights from Experience

### Railway Deployment Behavior
- **Auto-deployment is unreliable** - Railway doesn't always detect changes
- **Manual `railway up` required** - Most reliable deployment method
- **Version bumps help** - Changing VERSION constant forces proper rebuild
- **60 second cycle time** - Railway needs 60 seconds to cycle versions (new deployment or restart previous on failure)

### Common Issues & Solutions
- **Version not updating after 60s**: Check GitHub CI for syntax/test errors
- **Server not responding**: Check Railway logs with `railway logs --tail 20`
- **Deployment stuck**: Force redeploy with `railway redeploy`

### Version History Tracking
- Use semantic versioning consistently
- Tag releases: `git tag v2.7.4 && git push origin --tags`
- Document changes in commit messages
- Track progression: 2.1.0 → 2.7.4 (current)

## Monitoring & Rollback

### Health Checks
- `/api/status` endpoint shows version and basic health
- WebSocket connection test via web interface
- Server logs via `railway logs`

### Rollback Process
```bash
# If deployment fails, rollback to previous commit
git log --oneline -5  # Find previous good commit
git reset --hard <commit-hash>
git push origin main --force
railway up
```

## Future Improvements
- Consider automated deployment on successful CI
- Add proper health checks and monitoring
- Implement blue-green deployment for zero downtime
- Add automated rollback on deployment failure
