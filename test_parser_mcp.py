#!/usr/bin/env python3
"""
MCP API tests for the new command parser
"""
import requests
import json
import time

BASE_URL = "https://textspace-mud-dev-development.up.railway.app"

def test_mcp_command(command, username="parser-tester", expected_contains=None):
    """Test a command via MCP API"""
    print(f"\n{'='*60}")
    print(f"Testing: {command}")
    print(f"User: {username}")
    
    response = requests.post(
        f"{BASE_URL}/api/command",
        json={"command": command, "username": username},
        timeout=10
    )
    
    print(f"Status: {response.status_code}")
    
    try:
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")
        
        if expected_contains and result.get('success'):
            result_text = result.get('result', '')
            if expected_contains in result_text:
                print(f"✓ Found expected text: '{expected_contains}'")
            else:
                print(f"✗ Expected text not found: '{expected_contains}'")
                print(f"  Actual result: {result_text[:200]}")
        
        return result
    except Exception as e:
        print(f"Error parsing response: {e}")
        print(f"Raw response: {response.text[:500]}")
        return None

if __name__ == "__main__":
    print("="*60)
    print("PARSER FRAMEWORK TEST SUITE")
    print("="*60)
    
    # Login via MCP first
    print("\nLogging in via MCP...")
    login_response = requests.post(
        f"{BASE_URL}/api/mcp/login",
        json={"username": "parser-tester"},
        timeout=10
    )
    print(f"Login status: {login_response.status_code}")
    print(f"Login response: {login_response.json()}")
    
    # Test basic commands
    test_mcp_command("version", expected_contains="Text Spot")
    test_mcp_command("help", expected_contains="Available commands")
    test_mcp_command("whoami", expected_contains="parser-tester")
    
    # Test commands with arguments
    test_mcp_command("say Hello world", expected_contains="You say")
    
    # Test aliases
    test_mcp_command("l", expected_contains="Lobby")  # alias for look
    test_mcp_command("i", expected_contains="inventory")  # alias for inventory
    
    # Test multi-word arguments
    test_mcp_command("say this is a test message", expected_contains="You say")
    
    # Test quotes handling
    test_mcp_command('say "quoted text"', expected_contains="You say")
    
    # Test complex commands
    test_mcp_command("examine lobby", expected_contains="Lobby")
    
    # Test error cases
    test_mcp_command("", expected_contains="enter a command")
    test_mcp_command("invalidcommand", expected_contains="Unknown command")
    
    # Logout
    print("\nLogging out...")
    logout_response = requests.post(
        f"{BASE_URL}/api/mcp/logout",
        json={"username": "parser-tester"},
        timeout=10
    )
    print(f"Logout status: {logout_response.status_code}")
    
    print("\n" + "="*60)
    print("TEST SUITE COMPLETE")
    print("="*60)
