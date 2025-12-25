#!/bin/bash
# Configure Railway Development Environment for Develop Branch
# Run this on your local machine (where Railway CLI is installed)

echo "🚀 Configuring Railway Development Environment"
echo "=============================================="
echo ""

# Ensure we're in the project directory
cd "$(dirname "$0")" || exit 1

echo "📁 Project directory: $(pwd)"
echo ""

# Step 1: Link to the development project
echo "Step 1: Link to Railway development environment..."
echo "When prompted, select the development environment for textspace-mud"
echo ""

railway link

echo ""
echo "✅ Linked to Railway"
echo ""

# Step 2: Set environment variables
echo "Step 2: Setting environment variables..."
railway variables set PORT 8080
railway variables set RAILWAY_ENVIRONMENT_NAME development

echo ""
echo "Step 3: Verifying variables..."
railway variables list

echo ""
echo "Step 4: Current project and environment..."
railway project current
echo ""
railway environment current

echo ""
echo "Step 5: Deploying from develop branch..."
railway up

echo ""
echo "✅ Development environment setup complete!"
echo ""
echo "Verify deployment:"
echo "  - Check Railway dashboard for logs"
echo "  - Find the dev URL"
echo "  - Test: curl https://[dev-url]/api/status"
echo ""
echo "Your develop branch is now connected to Railway dev!"
