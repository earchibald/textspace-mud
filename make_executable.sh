#!/bin/bash
# Make all management scripts executable

echo "Making management scripts executable..."

chmod +x setup.py
chmod +x admin_tool.py
chmod +x monitor.py
chmod +x backup_tool.py
chmod +x test_suite.py
chmod +x migrate_v2.py
chmod +x test_enhanced.sh

echo "✅ All scripts are now executable"

echo ""
echo "Available management commands:"
echo "  ./setup.py setup-flat          # Quick setup for flat file mode"
echo "  ./setup.py setup-db            # Setup for database mode"
echo "  ./setup.py status              # Check system status"
echo "  ./admin_tool.py list           # List users"
echo "  ./monitor.py                   # Health check"
echo "  ./backup_tool.py create        # Create backup"
echo "  ./test_suite.py                # Run tests"
echo "  ./test_enhanced.sh             # Test enhanced server"
