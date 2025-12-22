#!/bin/bash
# Railway startup script for TextSpace server
# Handles persistent configuration setup

echo "🚀 Starting TextSpace Server on Railway"

# Check if we're on Railway
if [ "$RAILWAY_ENVIRONMENT" ]; then
    echo "📁 Setting up persistent configuration..."
    
    # Initialize configuration manager
    python3 config_manager.py init
    
    echo "✅ Persistent configuration ready"
else
    echo "🏠 Running in local development mode"
fi

# Start the server
echo "🌐 Starting web server..."
python3 server_web_only.py
