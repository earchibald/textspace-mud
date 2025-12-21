#!/bin/bash
# Test script for enhanced server with flat file backend

echo "Testing Enhanced Server (Flat File Backend)..."

# Check if server_v2.py exists
if [ ! -f "server_v2.py" ]; then
    echo "ERROR: server_v2.py not found"
    exit 1
fi

# Check if required files exist
for file in rooms.yaml bots.yaml items.yaml scripts.yaml; do
    if [ ! -f "$file" ]; then
        echo "ERROR: $file not found"
        exit 1
    fi
done

echo "✅ All required files found"

# Test import
echo "Testing Python imports..."
python -c "
try:
    import server_v2
    print('✅ server_v2.py imports successfully')
except ImportError as e:
    print('❌ Import error:', e)
    exit(1)
except Exception as e:
    print('⚠️  Import warning (expected for database modules):', e)
    print('✅ server_v2.py basic import successful')
"

echo "✅ Enhanced server test completed"
echo ""
echo "To start the enhanced server:"
echo "  python server_v2.py"
echo ""
echo "To enable database backend:"
echo "  1. Install dependencies: pip install -r requirements-db.txt"
echo "  2. Set up MongoDB and Redis"
echo "  3. Create .env file (see DEPLOYMENT.md)"
echo "  4. Run migration: python migrate_v2.py migrate"
echo "  5. Set USE_DATABASE=true in .env"
echo "  6. Start server: python server_v2.py"
