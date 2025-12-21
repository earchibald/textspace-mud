#!/bin/bash
# Release Testing Script
# Run this before every deployment

echo "🚀 Multi-User Text Space - Release Testing"
echo "=========================================="

# Activate virtual environment
source venv/bin/activate

echo "📋 Running Pre-Release Tests..."

# 1. Feature Test Suite
echo "🧪 Testing All Features..."
python test_features.py
FEATURE_EXIT=$?

# 2. Web Client Tests  
echo "🌐 Testing Web Interface..."
python test_web_client.py
WEB_EXIT=$?

# 3. System Health Check
echo "💊 Health Check..."
python monitor.py
HEALTH_EXIT=$?

# Results Summary
echo ""
echo "📊 Test Results Summary"
echo "======================="

if [ $FEATURE_EXIT -eq 0 ]; then
    echo "✅ Feature Tests: PASSED"
else
    echo "❌ Feature Tests: FAILED"
fi

if [ $WEB_EXIT -eq 0 ]; then
    echo "✅ Web Client Tests: PASSED"
else
    echo "❌ Web Client Tests: FAILED"
fi

if [ $HEALTH_EXIT -eq 0 ]; then
    echo "✅ Health Check: PASSED"
else
    echo "❌ Health Check: FAILED"
fi

# Overall result
if [ $FEATURE_EXIT -eq 0 ] && [ $WEB_EXIT -eq 0 ] && [ $HEALTH_EXIT -eq 0 ]; then
    echo ""
    echo "🎉 ALL TESTS PASSED - READY FOR DEPLOYMENT"
    exit 0
else
    echo ""
    echo "⚠️  SOME TESTS FAILED - REVIEW BEFORE DEPLOYMENT"
    exit 1
fi
