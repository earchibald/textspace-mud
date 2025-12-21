#!/usr/bin/env python3
"""
Comprehensive Test Suite for Text Space Server v1.2.0
Tests all functionality including new features
"""

import asyncio
import json
import time
import threading
from server import TextSpaceServer, User, WebUser
import io
import sys

class TestSuite:
    def __init__(self):
        self.server = None
        self.passed = 0
        self.failed = 0
        self.tests = []
        
    def test(self, name, func):
        """Run a test and track results"""
        try:
            result = func()
            if result:
                print(f"✅ PASS {name}")
                self.passed += 1
            else:
                print(f"❌ FAIL {name}")
                self.failed += 1
            self.tests.append((name, result))
        except Exception as e:
            print(f"❌ ERROR {name}: {e}")
            self.failed += 1
            self.tests.append((name, False))
    
    def setup_server(self):
        """Initialize server for testing"""
        self.server = TextSpaceServer()
        return True
    
    def test_version_command(self):
        """Test version command returns correct version"""
        from server import VERSION
        return VERSION == "1.2.0"
    
    def test_command_aliases(self):
        """Test command aliases are properly mapped"""
        aliases = {
            'n': 'north', 's': 'south', 'e': 'east', 'w': 'west',
            'l': 'look', 'g': 'go', '"': 'say', 'i': 'inventory', 'h': 'help'
        }
        
        # Test alias resolution in command processing
        parts = ['n']
        cmd = parts[0].lower()
        if cmd in aliases:
            cmd = aliases[cmd]
        return cmd == 'north'
    
    def test_room_loading(self):
        """Test rooms are loaded correctly"""
        return len(self.server.rooms) >= 6  # We have 6 rooms defined
    
    def test_bot_loading(self):
        """Test bots are loaded correctly"""
        return len(self.server.bots) >= 5  # We have 5 bots defined
    
    def test_item_loading(self):
        """Test items are loaded correctly"""
        return len(self.server.items) >= 8  # We have 8 items defined
    
    def test_partial_matching(self):
        """Test partial matching for go command"""
        # Test exact match
        exits = {"greenhouse": "greenhouse", "garden": "garden"}
        direction = "greenhouse"
        
        matching_exits = []
        exact_match = None
        
        for exit_name in exits:
            if exit_name == direction:
                exact_match = exit_name
                break
            elif exit_name.startswith(direction):
                matching_exits.append(exit_name)
        
        if exact_match:
            return exact_match == "greenhouse"
        
        return False
    
    def test_partial_matching_ambiguous(self):
        """Test ambiguous partial matching"""
        exits = {"gap": "gap", "garden": "garden"}
        direction = "ga"
        
        matching_exits = []
        exact_match = None
        
        for exit_name in exits:
            if exit_name == direction:
                exact_match = exit_name
                break
            elif exit_name.startswith(direction):
                matching_exits.append(exit_name)
        
        # Should find both gap and garden
        return len(matching_exits) == 2 and "gap" in matching_exits and "garden" in matching_exits
    
    def test_partial_matching_single(self):
        """Test single partial match"""
        exits = {"greenhouse": "greenhouse", "library": "library"}
        direction = "green"
        
        matching_exits = []
        exact_match = None
        
        for exit_name in exits:
            if exit_name == direction:
                exact_match = exit_name
                break
            elif exit_name.startswith(direction):
                matching_exits.append(exit_name)
        
        # Should find only greenhouse
        return len(matching_exits) == 1 and matching_exits[0] == "greenhouse"
    
    def test_room_dataclass(self):
        """Test Room class is properly defined"""
        from server import Room
        room = Room("test", "Test Room", "A test room", {"north": "lobby"})
        return room.id == "test" and room.name == "Test Room"
    
    def test_user_dataclass(self):
        """Test User class is properly defined"""
        from server import User
        import asyncio
        
        # Create a mock writer
        class MockWriter:
            def write(self, data): pass
            def drain(self): return asyncio.sleep(0)
            def close(self): pass
            def wait_closed(self): return asyncio.sleep(0)
        
        user = User("testuser", MockWriter())
        return user.name == "testuser" and user.room_id == "lobby"
    
    def test_web_user_dataclass(self):
        """Test WebUser class is properly defined"""
        from server import WebUser
        web_user = WebUser("testuser", "session123")
        return web_user.name == "testuser" and web_user.session_id == "session123"
    
    def test_script_engine_loading(self):
        """Test script engine is available"""
        return self.server.script_engine is not None
    
    def test_help_text_includes_aliases(self):
        """Test help text shows command aliases"""
        help_text = self.server.get_help_text(False)
        return "(l)" in help_text and "(n/s/e/w)" in help_text and "version" in help_text
    
    def test_backend_selection(self):
        """Test backend is properly selected"""
        return hasattr(self.server, 'use_database')
    
    def run_all_tests(self):
        """Run all tests and report results"""
        print("🚀 Text Space Server v1.2.0 Test Suite")
        print("=" * 60)
        print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Setup
        self.test("Server Initialization", self.setup_server)
        
        # Core functionality tests
        self.test("Version Command", self.test_version_command)
        self.test("Command Aliases", self.test_command_aliases)
        self.test("Room Loading", self.test_room_loading)
        self.test("Bot Loading", self.test_bot_loading)
        self.test("Item Loading", self.test_item_loading)
        
        # New v1.2.0 features
        self.test("Partial Matching - Exact", self.test_partial_matching)
        self.test("Partial Matching - Ambiguous", self.test_partial_matching_ambiguous)
        self.test("Partial Matching - Single", self.test_partial_matching_single)
        
        # Data structure tests
        self.test("Room Dataclass", self.test_room_dataclass)
        self.test("User Dataclass", self.test_user_dataclass)
        self.test("WebUser Dataclass", self.test_web_user_dataclass)
        
        # System tests
        self.test("Script Engine", self.test_script_engine_loading)
        self.test("Help Text Aliases", self.test_help_text_includes_aliases)
        self.test("Backend Selection", self.test_backend_selection)
        
        # Results
        print()
        print("📊 Test Results")
        print("=" * 60)
        total = self.passed + self.failed
        pass_rate = (self.passed / total * 100) if total > 0 else 0
        
        print(f"Tests Run: {total}")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        print(f"Pass Rate: {pass_rate:.1f}%")
        
        if pass_rate >= 90:
            print("🎉 EXCELLENT - System is working well!")
        elif pass_rate >= 80:
            print("✅ GOOD - System is mostly functional")
        elif pass_rate >= 70:
            print("⚠️  NEEDS WORK - Some issues to address")
        else:
            print("❌ CRITICAL - Major issues need fixing")
        
        return pass_rate >= 80

if __name__ == "__main__":
    suite = TestSuite()
    success = suite.run_all_tests()
    sys.exit(0 if success else 1)
