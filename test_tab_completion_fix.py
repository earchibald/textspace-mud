#!/usr/bin/env python3
"""Test tab completion for multi-word items in put/give commands"""

# Create a simple test class with the updated get_complex_completions logic
class TestCommandManager:
    def __init__(self):
        self.web_users = {}
        self.user_data = {}
        self.rooms = {}
        self.container_state = {}
        self.command_registry = {}
    
    def get_completion_context(self, username, context_type):
        """Get completion context based on type"""
        if context_type == "inventory_item":
            if username in self.user_data and 'inventory' in self.user_data[username]:
                return self.user_data[username]['inventory']
            return []
        elif context_type == "open_container":
            # Return containers that are open
            result = []
            for container, state in self.container_state.items():
                if state.get('state') == 'open':
                    result.append(container)
            return result
        elif context_type == "give_target":
            # Return NPCs and players in current room
            return ['Alice', 'Bob', 'Guard']
        return []
    
    def get_complex_completions(self, username, command_name, words, partial, full_text):
        """Get completions for complex grammar commands (put, give)"""
        completions = []
        
        if command_name == "put":
            # put ITEM [in CONTAINER]
            if len(words) == 1:  # "put "
                # Completing the item name
                items = self.get_completion_context(username, "inventory_item")
                for item in items:
                    if item.lower().startswith(partial):
                        completions.append({
                            'name': item,
                            'usage': f"put {item}",
                            'aliases': [],
                            'admin_only': False,
                            'type': 'argument'
                        })
            else:
                # len(words) >= 2: could be "put ITEM" or "put ITEM in" or multi-word item
                # Check if "in" is in the words (after the item)
                if "in" in words:
                    # "put ITEM in CONTAINER" - suggest containers
                    in_index = words.index("in")
                    containers = self.get_completion_context(username, "open_container")
                    for container in containers:
                        # Only show containers that start with partial, or all if partial is empty
                        if not partial or container.lower().startswith(partial):
                            completions.append({
                                'name': container,
                                'usage': f"put ... in {container}",
                                'aliases': [],
                                'admin_only': False,
                                'type': 'container'
                            })
                else:
                    # No "in" yet - determine if we should suggest preposition or still completing item
                    # Key insight: if full_text ends with space, we're at the preposition stage
                    # If it doesn't end with space but partial starts with 'i', could be "in"
                    # Otherwise still completing item name
                    
                    if full_text.endswith(' ') or (partial and "in".startswith(partial)):
                        # At preposition stage: suggest "in" and containers
                        if not partial or "in".startswith(partial):
                            completions.append({
                                'name': 'in',
                                'usage': f"put ... in <container>",
                                'aliases': [],
                                'admin_only': False,
                                'type': 'preposition'
                            })
                        # Also suggest open containers directly
                        containers = self.get_completion_context(username, "open_container")
                        for container in containers:
                            if container.lower().startswith(partial):
                                completions.append({
                                    'name': container,
                                    'usage': f"put ... in {container}",
                                    'aliases': [],
                                    'admin_only': False,
                                    'type': 'container'
                                })
                    else:
                        # Still completing the item name (multi-word item)
                        items = self.get_completion_context(username, "inventory_item")
                        for item in items:
                            if item.lower().startswith(partial):
                                completions.append({
                                    'name': item,
                                    'usage': f"put {item}",
                                    'aliases': [],
                                    'admin_only': False,
                                    'type': 'argument'
                                })
        
        elif command_name == "give":
            # give ITEM to TARGET
            if len(words) == 1:  # "give "
                # Completing the item name
                items = self.get_completion_context(username, "inventory_item")
                for item in items:
                    if item.lower().startswith(partial):
                        completions.append({
                            'name': item,
                            'usage': f"give {item}",
                            'aliases': [],
                            'admin_only': False,
                            'type': 'argument'
                        })
            else:
                # len(words) >= 2: could be "give ITEM" or "give ITEM to" or multi-word item
                # Check if "to" is in the words
                if "to" in words:
                    # "give ITEM to TARGET" - suggest targets
                    targets = self.get_completion_context(username, "give_target")
                    for target in targets:
                        # Only show targets that start with partial, or all if partial is empty
                        if not partial or target.lower().startswith(partial):
                            completions.append({
                                'name': target,
                                'usage': f"give ... to {target}",
                                'aliases': [],
                                'admin_only': False,
                                'type': 'target'
                            })
                else:
                    # No "to" yet - determine if we should suggest preposition or still completing item
                    # Key insight: if full_text ends with space, we're at the preposition stage
                    # If it doesn't end with space but partial starts with 't', could be "to"
                    # Otherwise still completing item name
                    
                    if full_text.endswith(' ') or (partial and "to".startswith(partial)):
                        # At preposition stage: suggest "to" and targets
                        if not partial or "to".startswith(partial):
                            completions.append({
                                'name': 'to',
                                'usage': f"give ... to <target>",
                                'aliases': [],
                                'admin_only': False,
                                'type': 'preposition'
                            })
                        # Also suggest targets directly
                        targets = self.get_completion_context(username, "give_target")
                        for target in targets:
                            if target.lower().startswith(partial):
                                completions.append({
                                    'name': target,
                                    'usage': f"give ... to {target}",
                                    'aliases': [],
                                    'admin_only': False,
                                    'type': 'target'
                                })
                    else:
                        # Still completing the item name (multi-word item)
                        items = self.get_completion_context(username, "inventory_item")
                        for item in items:
                            if item.lower().startswith(partial):
                                completions.append({
                                    'name': item,
                                    'usage': f"give {item}",
                                    'aliases': [],
                                    'admin_only': False,
                                    'type': 'argument'
                                })
        
        return completions


def test_put_completion_multiword():
    """Test put command completion with multi-word items"""
    manager = TestCommandManager()
    
    # Set up test user with inventory items
    username = "test_user"
    manager.web_users[username] = {
        'socket_id': 'test_socket',
        'current_room': 'room1'
    }
    
    # Add inventory items
    manager.user_data['test_user'] = {
        'inventory': ['Golden Coin', 'Blue Book', 'Red Key'],
        'location': 'room1'
    }
    
    # Add a container in the room
    manager.rooms['room1'] = {
        'name': 'Test Room',
        'description': 'A test room',
        'items': ['Treasure Chest'],
        'npcs': [],
        'exits': {}
    }
    
    # Add container state
    manager.container_state['Treasure Chest'] = {
        'state': 'open',
        'contents': []
    }
    
    print("Test 1: 'put ' - complete item name")
    words = ["put"]
    partial = ""
    full_text = "put "
    comps = manager.get_complex_completions(username, "put", words, partial, full_text)
    print(f"  Words: {words}, partial: '{partial}'")
    print(f"  Completions: {[c['name'] for c in comps]}")
    assert 'Golden Coin' in [c['name'] for c in comps], "Should suggest Golden Coin"
    print("  ✓ PASS\n")
    
    print("Test 2: 'put Golden Coin ' - should suggest 'in' and containers")
    words = ["put", "Golden", "Coin"]
    partial = ""
    full_text = "put Golden Coin "
    comps = manager.get_complex_completions(username, "put", words, partial, full_text)
    print(f"  Words: {words}, partial: '{partial}', ends with space: {full_text.endswith(' ')}")
    print(f"  Completions: {[(c['name'], c['type']) for c in comps]}")
    names = [c['name'] for c in comps]
    assert 'in' in names, f"Should suggest 'in' preposition, got {names}"
    assert 'Treasure Chest' in names, f"Should suggest 'Treasure Chest' container, got {names}"
    print("  ✓ PASS\n")
    
    print("Test 3: 'put Golden Coin i' - should suggest 'in' prefix match")
    words = ["put", "Golden", "Coin", "i"]
    partial = "i"
    full_text = "put Golden Coin i"
    comps = manager.get_complex_completions(username, "put", words, partial, full_text)
    print(f"  Words: {words}, partial: '{partial}'")
    print(f"  Completions: {[c['name'] for c in comps]}")
    assert 'in' in [c['name'] for c in comps], "Should suggest 'in' when partial='i'"
    print("  ✓ PASS\n")
    
    print("Test 4: 'put Golden Coin in ' - should suggest containers")
    words = ["put", "Golden", "Coin", "in"]
    partial = ""
    full_text = "put Golden Coin in "
    comps = manager.get_complex_completions(username, "put", words, partial, full_text)
    print(f"  Words: {words}, partial: '{partial}'")
    print(f"  Completions: {[c['name'] for c in comps]}")
    assert 'Treasure Chest' in [c['name'] for c in comps], "Should suggest Treasure Chest"
    print("  ✓ PASS\n")
    
    print("Test 5: 'put Golden Coin in T' - should match 'Treasure Chest'")
    words = ["put", "Golden", "Coin", "in", "T"]
    partial = "T"
    full_text = "put Golden Coin in T"
    comps = manager.get_complex_completions(username, "put", words, partial, full_text)
    print(f"  Words: {words}, partial: '{partial}'")
    print(f"  Completions: {[c['name'] for c in comps]}")
    assert 'Treasure Chest' in [c['name'] for c in comps], "Should match Treasure Chest"
    print("  ✓ PASS\n")
    
    print("Test 6: 'give Blue Book ' - should suggest 'to' and targets")
    words = ["give", "Blue", "Book"]
    partial = ""
    full_text = "give Blue Book "
    comps = manager.get_complex_completions(username, "give", words, partial, full_text)
    print(f"  Words: {words}, partial: '{partial}'")
    print(f"  Completions: {[(c['name'], c['type']) for c in comps]}")
    names = [c['name'] for c in comps]
    assert 'to' in names, f"Should suggest 'to' preposition, got {names}"
    print("  ✓ PASS\n")
    
    print("✓ All tests passed!")

if __name__ == '__main__':
    test_put_completion_multiword()
