#!/bin/bash
# Monitor server version deployment

echo "🔄 Monitoring server version deployment..."
echo "Target version: 2.3.2"
echo "Timeout: 90 seconds"
echo ""

start_time=$(date +%s)
timeout=90

while true; do
    current_time=$(date +%s)
    elapsed=$((current_time - start_time))
    
    if [ $elapsed -ge $timeout ]; then
        echo "❌ Timeout after 90 seconds - deployment may have failed"
        exit 1
    fi
    
    echo "⏱️  Checking version... (${elapsed}s elapsed)"
    
    # Check server status
    version=$(curl -s "https://exciting-liberation-production.up.railway.app/api/status" | python3 -c "import sys, json; print(json.load(sys.stdin)['version'])" 2>/dev/null)
    
    if [ "$version" = "2.3.2" ]; then
        echo "✅ Version 2.3.2 is now live! (after ${elapsed}s)"
        echo "🎉 Tab completion UI fix deployed successfully"
        exit 0
    elif [ -n "$version" ]; then
        echo "📊 Current version: $version (waiting for 2.3.2)"
    else
        echo "⚠️  Server not responding"
    fi
    
    sleep 5
done
