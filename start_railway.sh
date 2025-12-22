#!/bin/bash
# Railway startup script for TextSpace server

echo "🚀 Starting TextSpace Server on Railway"

# Check if we're on Railway and try to set up persistent config
if [ "$RAILWAY_ENVIRONMENT" ]; then
    echo "📁 Attempting to set up persistent configuration..."
    
    # Try to initialize configuration manager (non-blocking)
    python3 -c "
try:
    from config_manager import ConfigManager
    manager = ConfigManager()
    manager.initialize_persistent_config()
    print('✅ Persistent configuration initialized')
except Exception as e:
    print(f'⚠️ Config manager failed: {e}')
    print('Continuing with default configuration...')
" || echo "⚠️ Config setup failed, using defaults"
    
else
    echo "🏠 Running in local development mode"
fi

# Start the server
echo "🌐 Starting web server..."
exec python3 server_web_only.py
