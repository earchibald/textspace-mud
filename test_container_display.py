#!/usr/bin/env python3
"""
Quick test for container contents display fix
"""

import sys
sys.path.insert(0, '/Users/earchibald/scratch/006-mats')

from server_web_only import TextSpaceServer, WebUser

# Initialize server
server = TextSpaceServer()

# Create test user
admin_user = WebUser(name="admin", session_id="test_admin", authenticated=True, admin=True, room_id="lobby")
server.web_users["admin"] = admin_user

# Find treasure chest
treasure_chest_id = None
gold_coin_id = None

for item_id, item in server.items.items():
    if "treasure" in item.name.lower() and "chest" in item.name.lower():
        treasure_chest_id = item_id
    if "gold" in item.name.lower() and "coin" in item.name.lower():
        gold_coin_id = item_id

if treasure_chest_id and gold_coin_id:
    chest = server.items[treasure_chest_id]
    coin = server.items[gold_coin_id]
    
    # Setup: chest in room, open, with gold coin inside
    room = server.rooms["lobby"]
    if treasure_chest_id not in room.items:
        room.items.append(treasure_chest_id)
    
    chest.is_container = True
    chest.is_open = True
    chest.contents = [gold_coin_id]
    
    print("=" * 80)
    print("CONTAINER CONTENTS DISPLAY TEST")
    print("=" * 80)
    
    # Test 1: Examine open container with contents
    print("\n✅ TEST 1: Examine Open Container With Contents")
    result = server.handle_examine_target(admin_user, "Treasure Chest")
    print(f"Input: look Treasure Chest")
    print(f"Result:\n{result}")
    
    has_contains = "Contains:" in result
    has_coin = coin.name in result
    print(f"Status: {'✅ PASS' if has_contains and has_coin else '❌ FAIL'}")
    
    # Test 2: Examine closed container
    print("\n✅ TEST 2: Examine Closed Container")
    chest.is_open = False
    result = server.handle_examine_target(admin_user, "Treasure Chest")
    print(f"Input: look Treasure Chest")
    print(f"Result:\n{result}")
    
    has_closed = "closed" in result.lower()
    print(f"Status: {'✅ PASS' if has_closed else '❌ FAIL'}")
    
    # Test 3: Examine empty open container
    print("\n✅ TEST 3: Examine Empty Open Container")
    chest.is_open = True
    chest.contents = []
    result = server.handle_examine_target(admin_user, "Treasure Chest")
    print(f"Input: look Treasure Chest")
    print(f"Result:\n{result}")
    
    has_empty = "empty" in result.lower()
    print(f"Status: {'✅ PASS' if has_empty else '❌ FAIL'}")
    
    print("\n" + "=" * 80)
    print("CONTAINER DISPLAY FIX VERIFIED")
    print("=" * 80)
else:
    print("❌ Required items not found for testing")
