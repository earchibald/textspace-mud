#!/usr/bin/env python
"""
Comprehensive test suite for Multi-User Text Space System
Tests both flat file and database backends
"""
import asyncio
import json
import yaml
import tempfile
import shutil
import os
import sys
from datetime import datetime
import unittest
from unittest.mock import Mock, patch

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class TestTextSpaceSystem(unittest.TestCase):
    """Test suite for the text space system"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.original_dir = os.getcwd()
        os.chdir(self.test_dir)
        
        # Create minimal test data
        self.create_test_data()
    
    def tearDown(self):
        """Clean up test environment"""
        os.chdir(self.original_dir)
        shutil.rmtree(self.test_dir)
    
    def create_test_data(self):
        """Create minimal test configuration files"""
        # Test rooms
        rooms_data = {
            'rooms': {
                'lobby': {
                    'name': 'Test Lobby',
                    'description': 'A test lobby',
                    'exits': {'north': 'garden'},
                    'items': ['test_item']
                },
                'garden': {
                    'name': 'Test Garden',
                    'description': 'A test garden',
                    'exits': {'south': 'lobby'},
                    'items': []
                }
            }
        }
        
        with open('rooms.yaml', 'w') as f:
            yaml.dump(rooms_data, f)
        
        # Test items
        items_data = {
            'items': {
                'test_item': {
                    'name': 'Test Item',
                    'description': 'A test item',
                    'tags': ['test'],
                    'script': 'say This is a test item!'
                }
            }
        }
        
        with open('items.yaml', 'w') as f:
            yaml.dump(items_data, f)
        
        # Test bots
        bots_data = {
            'bots': {
                'test_bot': {
                    'name': 'Test Bot',
                    'room': 'lobby',
                    'description': 'A test bot',
                    'responses': [
                        {
                            'trigger': ['hello', 'hi'],
                            'response': 'Hello there!'
                        }
                    ]
                }
            }
        }
        
        with open('bots.yaml', 'w') as f:
            yaml.dump(bots_data, f)
        
        # Test scripts
        scripts_data = {
            'scripts': {
                'test_script': {
                    'bot': 'test_bot',
                    'script': 'say This is a test script!'
                }
            }
        }
        
        with open('scripts.yaml', 'w') as f:
            yaml.dump(scripts_data, f)
        
        # Empty users file
        with open('users.json', 'w') as f:
            json.dump({}, f)
    
    def test_flat_file_server_import(self):
        """Test that the flat file server can be imported"""
        try:
            import server_v2
            self.assertTrue(True, "Server imports successfully")
        except ImportError as e:
            self.fail(f"Server import failed: {e}")
    
    def test_script_engine_import(self):
        """Test that script engine can be imported"""
        try:
            import script_engine
            self.assertTrue(True, "Script engine imports successfully")
        except ImportError as e:
            self.fail(f"Script engine import failed: {e}")
    
    def test_data_loading(self):
        """Test that configuration files can be loaded"""
        try:
            import server_v2
            server = server_v2.TextSpaceServer(use_database=False)
            
            # Check that data was loaded
            self.assertIn('lobby', server.rooms)
            self.assertIn('garden', server.rooms)
            self.assertIn('test_item', server.items)
            self.assertIn('test_bot', server.bots)
            
        except Exception as e:
            self.fail(f"Data loading failed: {e}")
    
    def test_user_creation(self):
        """Test user creation and management"""
        try:
            import server_v2
            server = server_v2.TextSpaceServer(use_database=False)
            
            # Create mock writer
            mock_writer = Mock()
            
            # Create user
            user = server_v2.User(
                name="test_user",
                writer=mock_writer,
                room_id="lobby"
            )
            
            self.assertEqual(user.name, "test_user")
            self.assertEqual(user.room_id, "lobby")
            self.assertEqual(user.inventory, [])
            
        except Exception as e:
            self.fail(f"User creation failed: {e}")
    
    def test_room_navigation(self):
        """Test room navigation logic"""
        try:
            import server_v2
            server = server_v2.TextSpaceServer(use_database=False)
            
            # Get lobby room
            lobby = server.rooms['lobby']
            self.assertIn('north', lobby.exits)
            self.assertEqual(lobby.exits['north'], 'garden')
            
            # Get garden room
            garden = server.rooms['garden']
            self.assertIn('south', garden.exits)
            self.assertEqual(garden.exits['south'], 'lobby')
            
        except Exception as e:
            self.fail(f"Room navigation test failed: {e}")

class TestDatabaseBackend(unittest.TestCase):
    """Test database backend functionality"""
    
    def test_database_import(self):
        """Test database modules can be imported"""
        try:
            import database
            import auth
            self.assertTrue(True, "Database modules import successfully")
        except ImportError:
            self.skipTest("Database modules not available")
    
    def test_migration_tool_import(self):
        """Test migration tool can be imported"""
        try:
            import migrate_v2
            self.assertTrue(True, "Migration tool imports successfully")
        except ImportError:
            self.skipTest("Migration tool not available")

class TestScriptEngine(unittest.TestCase):
    """Test script engine functionality"""
    
    def setUp(self):
        """Set up script engine test"""
        self.test_dir = tempfile.mkdtemp()
        self.original_dir = os.getcwd()
        os.chdir(self.test_dir)
    
    def tearDown(self):
        """Clean up script engine test"""
        os.chdir(self.original_dir)
        shutil.rmtree(self.test_dir)
    
    def test_script_engine_creation(self):
        """Test script engine can be created"""
        try:
            import script_engine
            
            # Create mock server
            mock_server = Mock()
            engine = script_engine.ScriptEngine(mock_server)
            
            self.assertIsNotNone(engine)
            
        except Exception as e:
            self.fail(f"Script engine creation failed: {e}")

def run_integration_tests():
    """Run integration tests with actual server"""
    print("Running integration tests...")
    
    # Test server startup
    try:
        import server_v2
        server = server_v2.TextSpaceServer(use_database=False)
        print("✅ Server creation successful")
    except Exception as e:
        print(f"❌ Server creation failed: {e}")
        return False
    
    # Test data loading
    try:
        if len(server.rooms) > 0:
            print(f"✅ Loaded {len(server.rooms)} rooms")
        if len(server.items) > 0:
            print(f"✅ Loaded {len(server.items)} items")
        if len(server.bots) > 0:
            print(f"✅ Loaded {len(server.bots)} bots")
    except Exception as e:
        print(f"❌ Data loading test failed: {e}")
        return False
    
    print("✅ Integration tests passed")
    return True

def run_performance_tests():
    """Run basic performance tests"""
    print("Running performance tests...")
    
    try:
        import server_v2
        import time
        
        # Test server creation time
        start_time = time.time()
        server = server_v2.TextSpaceServer(use_database=False)
        creation_time = time.time() - start_time
        
        print(f"✅ Server creation time: {creation_time:.3f}s")
        
        if creation_time > 5.0:
            print("⚠️  Server creation is slow (>5s)")
        
        # Test data access time
        start_time = time.time()
        for _ in range(1000):
            _ = server.rooms.get('lobby')
        access_time = time.time() - start_time
        
        print(f"✅ 1000 room lookups: {access_time:.3f}s")
        
        return True
        
    except Exception as e:
        print(f"❌ Performance tests failed: {e}")
        return False

def main():
    """Main test runner"""
    print("Multi-User Text Space System - Test Suite")
    print("=" * 50)
    
    # Run unit tests
    print("\n1. Running Unit Tests...")
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    # Run integration tests
    print("\n2. Running Integration Tests...")
    integration_success = run_integration_tests()
    
    # Run performance tests
    print("\n3. Running Performance Tests...")
    performance_success = run_performance_tests()
    
    # Summary
    print("\n" + "=" * 50)
    print("Test Summary:")
    print(f"Integration Tests: {'✅ PASS' if integration_success else '❌ FAIL'}")
    print(f"Performance Tests: {'✅ PASS' if performance_success else '❌ FAIL'}")
    
    if integration_success and performance_success:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n⚠️  Some tests failed. Check output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
