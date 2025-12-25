#!/bin/bash
# Setup Railway development environment connection
# Run this script with appropriate permissions if needed

echo "🚀 Setting up Railway Development Environment Connection"
echo "==========================================================="
echo ""

# Check if railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Installing..."
    echo ""
    echo "Option 1: Install via npm (requires Node.js)"
    echo "  npm install -g @railway/cli"
    echo ""
    echo "Option 2: Install via Homebrew (macOS)"
    echo "  brew install railway"
    echo ""
    echo "Option 3: Download directly"
    echo "  https://railway.app/cli"
    echo ""
    exit 1
fi

echo "✅ Railway CLI found: $(railway --version)"
echo ""

# Check if git is configured
echo "📁 Git Configuration:"
git config --get remote.origin.url
echo ""

# Link to Railway development environment
echo "🔗 Linking to Railway development environment..."
echo "When prompted, select or create the 'textspace-mud-dev' project"
echo ""

railway link

echo ""
echo "✅ Linked to Railway development environment"
echo ""

# Verify connection
echo "📊 Current Railway Project:"
railway project current --json 2>/dev/null | grep -E "name|id" || railway project current

echo ""
echo "🌿 Setting up develop branch configuration..."
echo ""

# Check if .railway directory exists
if [ ! -d .railway ]; then
    echo "📁 Creating .railway directory..."
    mkdir -p .railway
fi

# Create or update the development environment config
cat > .railway/config-dev.json << 'EOF'
{
  "projectId": "YOUR_PROJECT_ID_HERE",
  "environmentId": "YOUR_ENVIRONMENT_ID_HERE",
  "services": {
    "textspace-mud": {
      "build": {
        "builder": "DOCKERFILE"
      },
      "deploy": {
        "startCommand": "./start_railway.sh",
        "healthcheckPath": "/",
        "healthcheckTimeout": 100,
        "restartPolicyType": "ON_FAILURE",
        "restartPolicyMaxRetries": 10
      }
    }
  }
}
EOF

echo "✅ Created .railway/config-dev.json"
echo ""

# Get project and environment IDs from current link
echo "🔍 Retrieving project and environment information..."
railway project current --json > /tmp/project.json 2>/dev/null

# Extract IDs if available
if [ -f /tmp/project.json ]; then
    echo "📊 Project Details:"
    cat /tmp/project.json | head -10
    echo ""
    echo "ℹ️  Update .railway/config-dev.json with actual projectId and environmentId"
fi

echo ""
echo "📝 Environment Variables Configuration:"
echo "========================================="
echo ""
echo "Set these in Railway Dashboard for the development environment:"
echo ""
echo "  PORT=8080"
echo "  RAILWAY_ENVIRONMENT_NAME=development"
echo ""
echo "Steps:"
echo "  1. Go to Railway Dashboard"
echo "  2. Select 'textspace-mud' service in development environment"
echo "  3. Click 'Variables' tab"
echo "  4. Add the above environment variables"
echo ""

echo "✅ Development environment connection setup complete!"
echo ""
echo "Next steps:"
echo "  1. Configure environment variables in Railway Dashboard"
echo "  2. Deploy: railway up"
echo "  3. Check status: curl https://[dev-url]/api/status"
echo ""
