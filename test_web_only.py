#!/usr/bin/env python3
"""
Comprehensive Test Suite for Web-Only Text Space Server v2.0.0
Tests all functional requirements with specific test protocols
"""

import unittest
import json
import time
import threading
from server_web_only import TextSpaceServer, WebUser

class TestWebOnlyTextSpace(unittest.TestCase):
    """Test suite for web-only Text Space server"""
    
    def setUp(self):
        """Set up test server"""
        self.server = TextSpaceServer()
        
    def test_01_server_initialization(self):
        """FR-01: Server initializes with web interface only"""
        self.assertIsNotNone(self.server.app)
        self.assertIsNotNone(self.server.socketio)
        self.assertGreater(len(self.server.rooms), 0)
        self.assertGreater(len(self.server.items), 0)
        self.assertGreater(len(self.server.bots), 0)
        
    def test_02_version_tracking(self):
        """FR-02: Version command returns correct version"""
        from server_web_only import VERSION
        self.assertEqual(VERSION, "2.0.0")
        
        # Test version command
        web_user = WebUser("testuser", "session123", admin=False)
        self.server.web_users["testuser"] = web_user
        response = self.server.process_command("testuser", "version")
        self.assertIn("2.0.0", response)
        
    def test_03_command_aliases(self):
        """FR-03: Single-letter command aliases work"""
        web_user = WebUser("testuser", "session123", admin=False)
        self.server.web_users["testuser"] = web_user
        
        # Test all aliases
        aliases = {
            'v': 'version',
            'h': 'help', 
            'l': 'look',
            'i': 'inventory',
            'n': 'north',
            's': 'south',
            'e': 'east', 
            'w': 'west'
        }
        
        for alias, full_cmd in aliases.items():
            # Test that alias produces same result as full command
            alias_response = self.server.process_command("testuser", alias)
            full_response = self.server.process_command("testuser", full_cmd)
            self.assertEqual(alias_response, full_response, f"Alias '{alias}' failed")
    
    def test_04_room_navigation(self):
        """FR-04: Room navigation with partial matching"""
        web_user = WebUser("testuser", "session123", room_id="garden")
        self.server.web_users["testuser"] = web_user
        self.server.rooms["garden"].users.add("testuser")
        
        # Test exact match
        response = self.server.move_user(web_user, "greenhouse")
        self.assertIn("Greenhouse", response)
        
        # Test partial match
        web_user.room_id = "garden"
        response = self.server.move_user(web_user, "green")
        self.assertIn("Greenhouse", response)
        
        # Test ambiguous match (if multiple exits start with same letters)
        # This would need specific room setup
        
    def test_05_user_authentication(self):
        """FR-05: User authentication and admin privileges"""
        # Test regular user
        web_user = WebUser("testuser", "session123", admin=False)
        self.assertFalse(web_user.admin)
        
        # Test admin user
        admin_user = WebUser("admin", "session456", admin=True)
        self.assertTrue(admin_user.admin)
        
    def test_06_help_system(self):
        """FR-06: Help system shows appropriate commands"""
        # Test regular user help
        web_user = WebUser("testuser", "session123", admin=False)
        self.server.web_users["testuser"] = web_user
        help_text = self.server.get_help_text(False)
        
        self.assertIn("look (l)", help_text)
        self.assertIn("version (v)", help_text)
        self.assertNotIn("Admin commands", help_text)
        
        # Test admin help
        admin_help = self.server.get_help_text(True)
        self.assertIn("Admin commands", admin_help)
        self.assertIn("teleport", admin_help)
        self.assertIn("kick", admin_help)
        
    def test_07_inventory_system(self):
        """FR-07: Inventory management"""
        web_user = WebUser("testuser", "session123", inventory=[])
        self.server.web_users["testuser"] = web_user
        
        # Test empty inventory
        response = self.server.get_inventory(web_user)
        self.assertIn("not carrying anything", response)
        
        # Test inventory with items
        web_user.inventory = ["magic_book"]
        response = self.server.get_inventory(web_user)
        self.assertIn("Magic Book", response)
        
    def test_08_room_descriptions(self):
        """FR-08: Room descriptions include all elements"""
        web_user = WebUser("testuser", "session123", room_id="lobby")
        self.server.web_users["testuser"] = web_user
        self.server.rooms["lobby"].users.add("testuser")
        
        description = self.server.get_room_description("lobby", "testuser")
        
        # Should include room name and description
        self.assertIn("Lobby", description)
        self.assertIn("entrance hall", description.lower())
        
        # Should include exits
        self.assertIn("Exits:", description)
        
    def test_09_user_list(self):
        """FR-09: Who command lists online users"""
        # Test empty user list
        response = self.server.get_who_list()
        self.assertIn("No users online", response)
        
        # Test with users
        self.server.web_users["user1"] = WebUser("user1", "session1")
        self.server.web_users["user2"] = WebUser("user2", "session2")
        
        response = self.server.get_who_list()
        self.assertIn("Online users (2)", response)
        self.assertIn("user1", response)
        self.assertIn("user2", response)
        
    def test_10_admin_commands(self):
        """FR-10: Admin commands work correctly"""
        admin_user = WebUser("admin", "session123", admin=True)
        self.server.web_users["admin"] = admin_user
        
        # Test teleport
        response = self.server.handle_teleport(admin_user, "library")
        self.assertIn("Library", response)
        
        # Test broadcast
        response = self.server.handle_broadcast(admin_user, "Test message")
        self.assertIn("Broadcast sent", response)
        
    def test_11_kick_command(self):
        """FR-11: Kick command removes users properly"""
        admin_user = WebUser("admin", "session123", admin=True)
        target_user = WebUser("baduser", "session456", room_id="lobby")
        
        self.server.web_users["admin"] = admin_user
        self.server.web_users["baduser"] = target_user
        self.server.rooms["lobby"].users.add("baduser")
        
        # Test kick
        response = self.server.handle_kick_user(admin_user, "baduser")
        self.assertIn("Kicked user: baduser", response)
        
        # Verify user removed
        self.assertNotIn("baduser", self.server.web_users)
        self.assertNotIn("baduser", self.server.rooms["lobby"].users)
        
    def test_12_switchuser_admin_only(self):
        """FR-12: Switchuser restricted to admin users"""
        # Test regular user denied
        regular_user = WebUser("testuser", "session123", admin=False)
        self.server.web_users["testuser"] = regular_user
        
        response = self.server.process_command("testuser", "switchuser admin")
        self.assertIn("Access denied", response)
        
        # Test admin user allowed
        admin_user = WebUser("admin", "session456", admin=True)
        self.server.web_users["admin"] = admin_user
        
        response = self.server.handle_switch_user(admin_user, "newuser")
        self.assertIn("Switched to user: newuser", response)
        
    def test_13_data_persistence(self):
        """FR-13: User data persistence"""
        web_user = WebUser("testuser", "session123", room_id="library", inventory=["magic_book"])
        
        # Test save
        self.server.save_user_data(web_user)
        
        # Test load
        loaded_data = self.server.load_user_data("testuser")
        self.assertIsNotNone(loaded_data)
        self.assertEqual(loaded_data["room_id"], "library")
        self.assertIn("magic_book", loaded_data["inventory"])
        
    def test_14_implicit_look_on_login(self):
        """FR-14: Users see room description on login"""
        # This would be tested in integration tests with actual SocketIO
        # For unit test, we verify the room description is generated
        description = self.server.get_room_description("lobby", "testuser")
        self.assertIsNotNone(description)
        self.assertGreater(len(description), 0)
        
    def test_15_server_name_configuration(self):
        """FR-15: Server name is configurable"""
        from server_web_only import SERVER_NAME
        self.assertEqual(SERVER_NAME, "The Text Spot")
        
    def test_16_web_only_architecture(self):
        """FR-16: No TCP/CLI functionality present"""
        # Verify no TCP-related attributes exist
        self.assertFalse(hasattr(self.server, 'tcp_server'))
        self.assertFalse(hasattr(self.server, 'connections'))
        self.assertFalse(hasattr(self.server, 'users'))  # Only web_users should exist
        
        # Verify only web users are supported
        self.assertTrue(hasattr(self.server, 'web_users'))
        self.assertTrue(hasattr(self.server, 'web_sessions'))

class TestProtocols:
    """Test protocols for manual/integration testing"""
    
    @staticmethod
    def print_test_protocols():
        """Print manual test protocols for each functional requirement"""
        protocols = {
            "FR-01 Server Initialization": [
                "1. Start server with 'python server_web_only.py'",
                "2. Verify web interface loads at http://localhost:8080",
                "3. Check logs show 'Web server starting'",
                "4. Verify no TCP server messages in logs"
            ],
            
            "FR-02 Version Tracking": [
                "1. Connect to web interface",
                "2. Login as any user",
                "3. Type 'version' or 'v'",
                "4. Verify response shows 'The Text Spot v2.0.0'"
            ],
            
            "FR-03 Command Aliases": [
                "1. Login to web interface",
                "2. Test each alias: v, h, l, i, n, s, e, w",
                "3. Verify each produces same result as full command",
                "4. Test 'g garden' for go command"
            ],
            
            "FR-04 Room Navigation": [
                "1. Login and go to garden",
                "2. Type 'g greenhouse' (exact match)",
                "3. Type 'g green' (partial match)",
                "4. Verify both work and show greenhouse description"
            ],
            
            "FR-05 User Authentication": [
                "1. Login as 'testuser' - verify no admin commands in help",
                "2. Login as 'admin' - verify admin commands shown",
                "3. Try admin command as regular user - verify denied"
            ],
            
            "FR-06 Help System": [
                "1. Type 'help' or 'h' as regular user",
                "2. Verify basic commands shown with aliases",
                "3. Login as admin, type 'help'",
                "4. Verify admin commands section appears"
            ],
            
            "FR-07 Inventory System": [
                "1. Type 'inventory' or 'i' when empty",
                "2. Pick up an item with 'get <item>'",
                "3. Check inventory again",
                "4. Drop item and verify inventory updates"
            ],
            
            "FR-08 Room Descriptions": [
                "1. Type 'look' or 'l' in any room",
                "2. Verify shows: name, description, exits, users, items",
                "3. Move to different room and repeat",
                "4. Have another user join room, verify they appear"
            ],
            
            "FR-09 User List": [
                "1. Type 'who' when alone - verify shows just you",
                "2. Have second user connect",
                "3. Type 'who' - verify shows both users with count",
                "4. Have user disconnect, verify count updates"
            ],
            
            "FR-10 Admin Commands": [
                "1. Login as admin",
                "2. Test 'teleport library' - verify moves to library",
                "3. Test 'broadcast Hello everyone' - verify all users see it",
                "4. Verify regular users cannot use these commands"
            ],
            
            "FR-11 Kick Command": [
                "1. Have two users connected",
                "2. Admin types 'kick <username>'",
                "3. Verify kicked user disconnected",
                "4. Type 'who' - verify user no longer listed"
            ],
            
            "FR-12 Switchuser Admin Only": [
                "1. Regular user types 'switchuser admin'",
                "2. Verify 'Access denied' message",
                "3. Admin types 'switchuser testuser'",
                "4. Verify successful switch with new room description"
            ],
            
            "FR-13 Data Persistence": [
                "1. Login, move to different room",
                "2. Disconnect and reconnect",
                "3. Verify still in same room",
                "4. Pick up items, disconnect/reconnect, verify items kept"
            ],
            
            "FR-14 Implicit Look": [
                "1. Login as new user",
                "2. Verify room description shown automatically",
                "3. No need to type 'look' command",
                "4. Should see room name, description, exits, etc."
            ],
            
            "FR-15 Server Name": [
                "1. Load web interface",
                "2. Verify page title shows 'The Text Spot'",
                "3. Verify header shows 'The Text Spot'",
                "4. Test SERVER_NAME environment variable override"
            ],
            
            "FR-16 Web Only Architecture": [
                "1. Verify no TCP port 8888 listening",
                "2. Try 'nc localhost 8888' - should fail",
                "3. Only web interface on port 8080 should work",
                "4. Check code has no TCP/CLI functionality"
            ]
        }
        
        print("=" * 60)
        print("MANUAL TEST PROTOCOLS - The Text Spot v2.0.0")
        print("=" * 60)
        
        for fr, steps in protocols.items():
            print(f"\n{fr}:")
            for step in steps:
                print(f"  {step}")
        
        print("\n" + "=" * 60)
        print("Run these tests after deploying to verify all functionality")
        print("=" * 60)

if __name__ == "__main__":
    # Run unit tests
    print("Running unit tests...")
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    # Print manual test protocols
    print("\n")
    TestProtocols.print_test_protocols()
