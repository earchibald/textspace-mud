#!/usr/bin/env python3
"""
Integration test for TextSpace MCP Server and Agent
Tests the complete system without requiring running TextSpace server
"""

import json
import sys
import os

def test_mcp_server():
    """Test MCP server functionality"""
    print("🔧 Testing MCP Server...")
    
    try:
        from textspace_mcp_server import TextSpaceManager
        manager = TextSpaceManager()
        
        # Test server status
        status = manager.get_server_status()
        assert "running" in status
        assert "version" in status
        print("  ✅ Server status check works")
        
        # Test config reading
        try:
            with open("rooms.yaml", "r") as f:
                content = f.read()
            print("  ✅ Config file reading works")
        except Exception as e:
            print(f"  ⚠️  Config reading: {e}")
        
        # Test validation
        test_yaml = """
rooms:
  test:
    name: "Test Room"
    description: "Test"
    exits: {}
    items: []
"""
        validation = manager.validate_yaml_config("rooms", test_yaml)
        assert validation["valid"] == True
        print("  ✅ YAML validation works")
        
        # Test version increment (dry run)
        current_version = status["version"]
        print(f"  ✅ Current version: {current_version}")
        
        return True
    except Exception as e:
        print(f"  ❌ MCP Server test failed: {e}")
        return False

def test_agent():
    """Test TextSpace agent"""
    print("🤖 Testing TextSpace Agent...")
    
    try:
        from textspace_agent import TextSpaceAgent
        agent = TextSpaceAgent()
        
        # Test health check (should work even with server down)
        health = agent.health_check()
        assert "status" in health
        assert "message" in health
        print(f"  ✅ Health check: {health['status']} - {health['message']}")
        
        return True
    except Exception as e:
        print(f"  ❌ Agent test failed: {e}")
        return False

def test_mcp_config():
    """Test MCP configuration"""
    print("⚙️  Testing MCP Configuration...")
    
    try:
        config_path = ".kiro/settings/mcp.json"
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                config = json.load(f)
            
            assert "mcpServers" in config
            assert "textspace" in config["mcpServers"]
            print("  ✅ MCP configuration exists and is valid")
            return True
        else:
            print("  ⚠️  MCP configuration file not found")
            return False
    except Exception as e:
        print(f"  ❌ MCP config test failed: {e}")
        return False

def main():
    """Run all integration tests"""
    print("🚀 TextSpace MCP Integration Test Suite")
    print("=" * 50)
    
    tests = [
        ("MCP Server", test_mcp_server),
        ("TextSpace Agent", test_agent),
        ("MCP Configuration", test_mcp_config)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        result = test_func()
        results.append((test_name, result))
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Summary: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! TextSpace MCP system is ready.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
