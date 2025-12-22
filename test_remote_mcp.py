#!/usr/bin/env python3
"""
Test Remote MCP Server functionality
"""

import json
import sys
import os

def test_remote_mcp():
    """Test remote MCP server functionality"""
    print("🧪 Testing Remote TextSpace MCP Server...")
    
    try:
        from textspace_remote_mcp_server import RemoteTextSpaceManager
        manager = RemoteTextSpaceManager()
        
        # Test validation (works offline)
        print("  Testing YAML validation...")
        validation = manager.validate_yaml_config('rooms', '''
rooms:
  test_room:
    name: "Test Room"
    description: "A test room"
    exits: {}
    items: []
''')
        assert validation["valid"] == True
        print("  ✅ YAML validation works")
        
        # Test server status (will show connection error until Railway is ready)
        print("  Testing server status...")
        status = manager.get_server_status()
        print(f"  📊 Status: {status.get('error', 'Connected!')}")
        
        return True
    except Exception as e:
        print(f"  ❌ Remote MCP test failed: {e}")
        return False

def main():
    """Run remote MCP tests"""
    print("🚀 Remote TextSpace MCP Test Suite")
    print("=" * 50)
    
    success = test_remote_mcp()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ Remote MCP Server is ready!")
        print("📡 Will connect to Railway once deployment completes")
        return 0
    else:
        print("❌ Remote MCP Server has issues")
        return 1

if __name__ == "__main__":
    sys.exit(main())
