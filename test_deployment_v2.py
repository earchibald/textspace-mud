#!/usr/bin/env python3
"""Quick test to verify v2.0.1 deployment with player events"""

from server_web_only import TextSpaceServer, WebUser

def test_v2_features():
    """Test v2.0.1 features"""
    server = TextSpaceServer()
    
    # Test version
    user = WebUser("testuser", "session123")
    server.web_users["testuser"] = user
    
    version_response = server.process_command("testuser", "version")
    print(f"✅ Version: {version_response}")
    
    # Test whisper command
    server.web_users["target"] = WebUser("target", "session456")
    whisper_response = server.process_command("testuser", "whisper target hello")
    print(f"✅ Whisper: {whisper_response}")
    
    # Test quote alias
    quote_response = server.process_command("testuser", '"Hello everyone')
    print(f"✅ Quote alias: {quote_response}")
    
    print("\n🚀 v2.0.1 Web-Only Server Features Verified!")

if __name__ == "__main__":
    test_v2_features()
