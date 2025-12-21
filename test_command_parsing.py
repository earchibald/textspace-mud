#!/usr/bin/env python3
"""Test most-significant match command parsing"""

from server_web_only import TextSpaceServer, WebUser

def test_command_parsing():
    """Test the new command parsing system"""
    server = TextSpaceServer()
    
    # Create test users
    regular_user = WebUser("user", "session1", admin=False)
    admin_user = WebUser("admin", "session2", admin=True)
    server.web_users["user"] = regular_user
    server.web_users["admin"] = admin_user
    
    print("🧪 Testing Most-Significant Match Command Parsing")
    print("=" * 50)
    
    # Test exact aliases
    print("\n📍 Exact Aliases:")
    test_cases = [
        ("w", "west"),
        ("n", "north"), 
        ("l", "look"),
        ("h", "help"),
        ("v", "version")
    ]
    
    for input_cmd, expected in test_cases:
        result = server.resolve_command(input_cmd, False)
        status = "✅" if result == expected else "❌"
        print(f"  {status} '{input_cmd}' → '{result}' (expected: {expected})")
    
    # Test partial matches
    print("\n📍 Partial Matches:")
    test_cases = [
        ("wh", "whisper"),
        ("we", "west"),
        ("wes", "west"),
        ("inv", "inventory"),
        ("exa", "examine"),
        ("tel", "teleport", True),  # admin only
        ("bro", "broadcast", True)  # admin only
    ]
    
    for case in test_cases:
        input_cmd = case[0]
        expected = case[1]
        is_admin = case[2] if len(case) > 2 else False
        
        result = server.resolve_command(input_cmd, is_admin)
        status = "✅" if result == expected else "❌"
        admin_note = " (admin)" if is_admin else ""
        print(f"  {status} '{input_cmd}' → '{result}' (expected: {expected}){admin_note}")
    
    # Test ambiguous matches
    print("\n📍 Ambiguous Matches:")
    ambiguous_cases = [
        ("e", ["east", "examine", "exam"]),  # Should be ambiguous
        ("g", ["get", "go"])  # Should be ambiguous (g alias overrides)
    ]
    
    for input_cmd, expected_matches in ambiguous_cases:
        result = server.resolve_command(input_cmd, False)
        if result.startswith("AMBIGUOUS:"):
            matches = result.split(":")[1].split(",")
            status = "✅" if set(matches) == set(expected_matches) else "❌"
            print(f"  {status} '{input_cmd}' → ambiguous: {matches}")
        else:
            print(f"  ❌ '{input_cmd}' → '{result}' (expected ambiguous)")
    
    # Test full command processing with ambiguous handling
    print("\n📍 Full Command Processing:")
    response = server.process_command("user", "e")
    print(f"  Command 'e': {response}")
    
    response = server.process_command("user", "wh hello")
    print(f"  Command 'wh hello': {response}")
    
    print("\n🎯 Most-Significant Match Parsing Complete!")

if __name__ == "__main__":
    test_command_parsing()
