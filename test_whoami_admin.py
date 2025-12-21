#!/usr/bin/env python3
"""Test whoami command and admin help display fix"""

from server_web_only import TextSpaceServer, WebUser

def test_whoami_and_admin_help():
    """Test whoami command and admin help display"""
    server = TextSpaceServer()
    
    print("🧪 Testing whoami and admin help fixes")
    print("=" * 50)
    
    # Test regular user
    regular_user = WebUser("testing", "session1", admin=False)
    server.web_users["testing"] = regular_user
    
    print("\n📍 Regular User Tests:")
    whoami_response = server.process_command("testing", "whoami")
    print(f"  whoami: {whoami_response}")
    
    help_response = server.get_help_text(False)
    has_admin_section = "Admin commands:" in help_response
    print(f"  Admin commands in help: {has_admin_section} (should be False)")
    
    # Test admin user
    admin_user = WebUser("tester-admin", "session2", admin=True)
    server.web_users["tester-admin"] = admin_user
    
    print("\n📍 Admin User Tests:")
    whoami_response = server.process_command("tester-admin", "whoami")
    print(f"  whoami: {whoami_response}")
    
    help_response = server.get_help_text(True)
    has_admin_section = "Admin commands:" in help_response
    print(f"  Admin commands in help: {has_admin_section} (should be True)")
    
    # Test version
    version_response = server.process_command("testing", "version")
    print(f"\n📍 Version: {version_response}")
    
    print("\n✅ Tests completed!")

if __name__ == "__main__":
    test_whoami_and_admin_help()
