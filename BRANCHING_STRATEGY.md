# TextSpace Development Branch Workflow

## Branch Strategy

```
main (production) ← Release PRs only
  ↑
  │ (Pull Requests from develop)
  │
develop (development) ← Feature branches merge here
  ↑
  ├─ feature/new-verb
  ├─ bugfix/parser-issue
  └─ refactor/command-system
```

## Workflows

### Creating a Feature Branch

```bash
# 1. Start from develop and pull latest
git checkout develop
git pull origin develop

# 2. Create feature branch
git checkout -b feature/descriptive-name

# 3. Make changes, test locally
python3 server_web_only.py
# Test functionality...

# 4. Commit with semantic messages
git add .
git commit -m "feat: add put/give verbs with complex grammar"

# 5. Push to your branch
git push origin feature/descriptive-name

# 6. Create Pull Request on GitHub
# Target: develop branch
# Use PR template to describe changes
```

### Merging to Develop (Auto-Deploy to Dev Railway)

```bash
# On GitHub:
# 1. Create PR from feature/xxx → develop
# 2. Pass code review
# 3. Merge to develop

# Automatic: develop branch deploys to Railway Dev environment
# Monitor: railway logs --environment development
```

### Promoting to Production (Main Branch)

```bash
# On GitHub:
# 1. When develop is stable and tested in Dev Railway
# 2. Create PR from develop → main
# 3. Code review + approval
# 4. Merge to main

# Automatic: main branch deploys to Railway Production environment
# Monitor: railway logs --environment production
```

## Development Workflow Checklist

### Before Creating Pull Request
- [ ] Code runs locally without errors
- [ ] Dependencies added to requirements.txt if needed
- [ ] Changes tested on devcontainer
- [ ] No hardcoded values or debug statements
- [ ] Commit messages follow semantic format

### PR Template (for GitHub)

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## How to Test
Steps to verify the changes work

## Testing Evidence
- Screenshots or logs showing it works
- Manual test results

## Checklist
- [ ] Code follows project style
- [ ] No new warnings or errors
- [ ] Changes are well-documented
- [ ] Testing completed locally
```

### Code Review Checklist
- [ ] Code is readable and maintainable
- [ ] Changes follow the proposed design
- [ ] No regressions introduced
- [ ] Edge cases handled
- [ ] Documentation updated if needed

## Deployment Timeline

```
Monday: Feature development & testing in local devcontainer
Tuesday: Create PR to develop, deploy to Dev Railway
Wednesday: Test in Dev Railway, get approvals
Thursday: Create PR to main, prepare for production
Friday: Merge to main, deploy to Production Railway
```

## Rolling Back Changes

### If develop has issues
```bash
# Find the problematic commit
git log --oneline develop

# Revert it
git revert <commit-hash>
git push origin develop

# This redeploys Dev Railway with the revert
```

### If production has critical issues
```bash
# Switch to main branch
git checkout main

# Find last good commit
git log --oneline

# Create hotfix branch
git checkout -b hotfix/critical-fix

# Fix issue, test locally, then:
git add .
git commit -m "fix: critical issue description"
git push origin hotfix/critical-fix

# Create PR to main
# After merge, redeploy production
railway up --environment production
```

## Continuous Deployment Notes

- **develop → Dev Railway**: Automatic on merge
- **main → Prod Railway**: Automatic on merge (or manual `railway up`)
- **Feature branches**: Deploy locally only during development
- **Hotfixes**: Bypass develop, go straight to main

## Environment Variables per Branch

| Branch | Environment | RAILWAY_ENVIRONMENT_NAME | PORT | URL |
|--------|-------------|--------------------------|------|-----|
| develop | Dev | development | 8080 | https://textspace-dev.railway.app |
| main | Prod | production | 8080 | https://exciting-liberation-production.up.railway.app |
| feature/* | Local | (not set) | 8080 | http://localhost:8080 |

## Useful Commands

```bash
# List all branches
git branch -a

# Switch branches
git checkout develop
git checkout -b feature/name

# Push new branch
git push -u origin feature/name

# Check current branch
git branch --show-current

# View develop updates
git fetch origin
git log --oneline origin/develop

# Delete local branch
git branch -d feature/name

# Delete remote branch
git push origin --delete feature/name
```

## Support

For issues with the workflow:
1. Check that your feature branch is based on latest develop
2. Resolve merge conflicts locally
3. Test thoroughly before pushing
4. Contact maintainer if deployment issues occur

