#!/usr/bin/env python
"""
Web client testing suite using SocketIO client
Tests the live Railway deployment
"""
import socketio
import time
import json
import asyncio
from datetime import datetime

class WebClientTester:
    def __init__(self, url="https://exciting-liberation-production.up.railway.app"):
        self.url = url
        self.sio = socketio.Client()
        self.messages = []
        self.room_info = None
        self.login_success = False
        
        # Setup event handlers
        self.setup_handlers()
    
    def setup_handlers(self):
        @self.sio.event
        def connect():
            print("✅ Connected to server")
        
        @self.sio.event
        def disconnect():
            print("❌ Disconnected from server")
        
        @self.sio.event
        def message(data):
            msg = data.get('text', '')
            self.messages.append(msg)
            print(f"📨 Message: {msg}")
        
        @self.sio.event
        def login_response(data):
            self.login_success = data.get('success', False)
            if self.login_success:
                print(f"✅ Login successful (admin: {data.get('admin', False)})")
            else:
                print(f"❌ Login failed: {data.get('message', 'Unknown error')}")
        
        @self.sio.event
        def room_info(data):
            self.room_info = data
            print(f"🏠 Room: {data.get('name', 'Unknown')}")
            print(f"   Exits: {', '.join(data.get('exits', []))}")
            if data.get('bots'):
                print(f"   Bots: {', '.join(data.get('bots', []))}")
            if data.get('items'):
                print(f"   Items: {', '.join(data.get('items', []))}")
    
    def connect(self):
        """Connect to the server"""
        try:
            self.sio.connect(self.url)
            time.sleep(1)  # Wait for connection
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def login(self, username):
        """Login with username"""
        print(f"🔑 Logging in as '{username}'...")
        self.sio.emit('login', {'username': username})
        time.sleep(2)  # Wait for response
        return self.login_success
    
    def send_command(self, command):
        """Send a command and wait for response"""
        print(f"⌨️  Command: {command}")
        initial_msg_count = len(self.messages)
        self.sio.emit('command', {'command': command})
        
        # Wait for response (up to 5 seconds)
        for _ in range(50):
            if len(self.messages) > initial_msg_count:
                return self.messages[-1]
            time.sleep(0.1)
        
        return None
    
    def test_basic_commands(self):
        """Test basic command functionality"""
        print("\n🧪 Testing Basic Commands")
        print("=" * 40)
        
        tests = [
            ("help", "should show command list"),
            ("look", "should show room description"),
            ("inventory", "should show inventory"),
            ("who", "should show online users"),
        ]
        
        results = {}
        for command, expected in tests:
            response = self.send_command(command)
            success = response is not None and len(response) > 0
            results[command] = success
            status = "✅" if success else "❌"
            print(f"{status} {command}: {expected}")
            if response:
                print(f"   Response: {response[:100]}...")
        
        return results
    
    def test_movement(self):
        """Test room movement"""
        print("\n🚶 Testing Movement")
        print("=" * 40)
        
        # Get initial room
        initial_room = self.room_info.get('name') if self.room_info else None
        print(f"Starting room: {initial_room}")
        
        # Try to move north
        response = self.send_command("north")
        time.sleep(1)  # Wait for room info update
        
        new_room = self.room_info.get('name') if self.room_info else None
        moved = new_room != initial_room
        
        status = "✅" if moved else "❌"
        print(f"{status} Movement north: {initial_room} → {new_room}")
        
        # Try to move back
        if moved:
            response = self.send_command("south")
            time.sleep(1)
            back_room = self.room_info.get('name') if self.room_info else None
            back_success = back_room == initial_room
            status = "✅" if back_success else "❌"
            print(f"{status} Movement south: {new_room} → {back_room}")
            return moved and back_success
        
        return moved
    
    def test_chat(self):
        """Test chat functionality"""
        print("\n💬 Testing Chat")
        print("=" * 40)
        
        test_message = f"Test message at {datetime.now().strftime('%H:%M:%S')}"
        response = self.send_command(f"say {test_message}")
        
        success = response is not None and "You say:" in response
        status = "✅" if success else "❌"
        print(f"{status} Chat: {response}")
        
        return success
    
    def test_persistence(self):
        """Test user persistence by reconnecting"""
        print("\n💾 Testing Persistence")
        print("=" * 40)
        
        # Move to a different room
        self.send_command("north")
        time.sleep(1)
        room_before = self.room_info.get('name') if self.room_info else None
        
        # Disconnect and reconnect
        print("🔄 Disconnecting and reconnecting...")
        self.sio.disconnect()
        time.sleep(2)
        
        # Reconnect
        if self.connect():
            if self.login("test_persistence"):
                time.sleep(2)
                room_after = self.room_info.get('name') if self.room_info else None
                
                success = room_before == room_after
                status = "✅" if success else "❌"
                print(f"{status} Persistence: {room_before} == {room_after}")
                return success
        
        return False
    
    def run_full_test(self):
        """Run complete test suite"""
        print("🚀 Starting Web Client Test Suite")
        print("=" * 50)
        print(f"Target: {self.url}")
        print()
        
        # Connect
        if not self.connect():
            return False
        
        # Login
        if not self.login("test_admin"):
            return False
        
        time.sleep(2)  # Wait for initial room info
        
        # Run tests
        results = {}
        results['basic_commands'] = self.test_basic_commands()
        results['movement'] = self.test_movement()
        results['chat'] = self.test_chat()
        results['persistence'] = self.test_persistence()
        
        # Summary
        print("\n📊 Test Results Summary")
        print("=" * 50)
        
        all_passed = True
        for test_name, result in results.items():
            if isinstance(result, dict):
                # Basic commands test
                passed = all(result.values())
                failed_commands = [cmd for cmd, success in result.items() if not success]
            else:
                # Single test
                passed = result
                failed_commands = []
            
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{status} {test_name.replace('_', ' ').title()}")
            
            if failed_commands:
                print(f"   Failed: {', '.join(failed_commands)}")
            
            if not passed:
                all_passed = False
        
        print()
        overall_status = "✅ ALL TESTS PASSED" if all_passed else "❌ SOME TESTS FAILED"
        print(f"🎯 Overall: {overall_status}")
        
        self.sio.disconnect()
        return all_passed

def main():
    """Run the test suite"""
    tester = WebClientTester()
    success = tester.run_full_test()
    return 0 if success else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
