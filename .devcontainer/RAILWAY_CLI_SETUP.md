# Railway CLI Setup - Develop Environment Connection

Since the devcontainer doesn't have npm/Node.js, you'll need to run Railway CLI commands on your local machine.

## Prerequisites

Install Railway CLI on your local machine:

### macOS
```bash
brew install railway
```

### Linux/Windows (via curl)
```bash
curl -L https://railway.app/cli/install.sh | bash
```

Or download from: https://railway.app/cli

## Commands to Run

Once Railway CLI is installed, run these commands in your terminal (on your local machine):

```bash
# Step 1: Authenticate with Railway
railway login

# Step 2: Navigate to project directory
cd /path/to/textspace-mud

# Step 3: Link to the development environment
railway link
# Select: textspace-mud (development environment)

# Step 4: Set environment variables
railway variables set PORT 8080
railway variables set RAILWAY_ENVIRONMENT_NAME development

# Step 5: Verify setup
railway variables list
railway project current
railway environment current

# Step 6: Deploy
railway up
```

## What These Commands Do

| Command | Purpose |
|---------|---------|
| `railway login` | Authenticate with your Railway account |
| `railway link` | Connect to the Railway project and environment |
| `railway variables set KEY value` | Set environment variables |
| `railway variables list` | List all environment variables |
| `railway project current` | Show current project |
| `railway environment current` | Show current environment |
| `railway up` | Deploy the current branch |

## Alternative: Use the Script

We've created a helper script that runs all commands:

```bash
# On your local machine, in the project directory
bash setup-railway-dev-cli.sh
```

This will:
1. Prompt you to select the development environment
2. Set PORT and RAILWAY_ENVIRONMENT_NAME variables
3. Verify the setup
4. Deploy from develop branch

## Manual Dashboard Method (if CLI fails)

If Railway CLI isn't available, do this in Railway Dashboard:

1. Go to https://railway.app/dashboard
2. Select `textspace-mud` project → `development` environment
3. Click the `textspace-mud` service
4. Settings (gear icon) > Git section
5. Under "Deploy from branch": select `develop`
6. Variables tab: add `PORT=8080` and `RAILWAY_ENVIRONMENT_NAME=development`
7. Save and deploy

## Verification

After setup, verify it's working:

```bash
# Get the dev environment URL
railway open

# Test the health endpoint
curl https://[dev-url]/api/status | python3 -m json.tool

# Or check logs
railway logs --tail 50
```

## Troubleshooting

**"railway: command not found"**
- Make sure Railway CLI is installed: `railway --version`
- Install from: https://railway.app/cli

**"Project not found"**
- Run `railway login` first to authenticate
- Make sure you're in the correct project directory

**"Wrong environment selected"**
- Run `railway link` again and select development environment
- Or set: `railway environment current` to show what's selected

**"Variables not applying"**
- Redeploy: `railway up`
- Or use dashboard: Settings > Variables

## Next Steps

Once configured:
1. Push to develop: `git push origin develop`
2. Railway automatically deploys
3. Monitor in dashboard or: `railway logs --follow`
4. Test health endpoint
5. Create PRs to main when ready for production

