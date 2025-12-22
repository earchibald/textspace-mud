#!/usr/bin/env python3
"""
TextSpace Room Map Generator
Creates a visual ASCII map of the room layout
"""

import yaml
import sys

def generate_map():
    """Generate ASCII map of TextSpace rooms"""
    
    # Parse the rooms data
    rooms_data = """
rooms:
  garden:
    description: A peaceful garden with colorful flowers and a small fountain.
    exits:
      greenhouse: greenhouse
      south: lobby
    items:
    - flower_seeds
    name: The Garden
  greenhouse:
    description: A warm, humid space filled with exotic plants and butterflies.
    exits:
      garden: garden
    name: The Greenhouse
  library:
    description: Tall shelves filled with books of all kinds. A cozy reading nook sits in the corner.
    exits:
      study: study
      west: lobby
    items:
    - magic_book
    - story_scroll
    name: The Library
  lobby:
    description: A welcoming entrance hall with soft lighting. Doors lead in various directions.
    exits:
      east: library
      north: garden
      south: playground
    items:
    - treasure_chest
    name: The Lobby
  mcp_test_room:
    description: A room added via Remote MCP Server
    exits:
      lobby: lobby
    items: []
    name: MCP Test Room
  playground:
    description: A fun space with colorful toys and games. Laughter echoes here.
    exits:
      north: lobby
    name: The Playground
  study:
    description: A quiet room with desks and learning materials. Perfect for focused activities.
    exits:
      library: library
    name: The Study Room
"""
    
    rooms = yaml.safe_load(rooms_data)['rooms']
    
    # Create ASCII map
    print("🗺️  TextSpace Room Map")
    print("=" * 60)
    print()
    
    # Top row: Greenhouse
    print("                    ┌─────────────────┐")
    print("                    │   Greenhouse    │")
    print("                    │  🌿 Plants &    │")
    print("                    │   Butterflies   │")
    print("                    └─────────┬───────┘")
    print("                              │")
    
    # Second row: Garden
    print("                    ┌─────────┴───────┐")
    print("                    │     Garden      │")
    print("                    │  🌸 Flowers &   │")
    print("                    │    Fountain     │")
    print("                    │  [flower_seeds] │")
    print("                    └─────────┬───────┘")
    print("                              │")
    
    # Third row: Library - Lobby - MCP Test Room
    print("┌─────────────────┐           │           ┌─────────────────┐")
    print("│     Library     │           │           │  MCP Test Room  │")
    print("│  📚 Books &     │───────────┼───────────│   🧪 Testing    │")
    print("│  Reading Nook   │           │           │     Space       │")
    print("│ [magic_book,    │           │           │      []         │")
    print("│  story_scroll]  │           │           │                 │")
    print("└─────────┬───────┘           │           └─────────────────┘")
    print("          │         ┌─────────┴───────┐")
    print("          │         │     Lobby       │")
    print("          │         │  🏛️ Entrance    │")
    print("          │         │     Hall        │")
    print("          │         │ [treasure_chest]│")
    print("          │         └─────────┬───────┘")
    print("          │                   │")
    
    # Fourth row: Study and Playground
    print("┌─────────┴───────┐           │")
    print("│   Study Room    │           │")
    print("│  📖 Desks &     │           │")
    print("│   Learning      │           │")
    print("│   Materials     │           │")
    print("│      []         │           │")
    print("└─────────────────┘           │")
    print("                    ┌─────────┴───────┐")
    print("                    │   Playground    │")
    print("                    │  🎮 Toys &      │")
    print("                    │     Games       │")
    print("                    │      []         │")
    print("                    └─────────────────┘")
    
    print()
    print("=" * 60)
    print("📊 Room Statistics:")
    print(f"   Total Rooms: {len(rooms)}")
    print(f"   Rooms with Items: {sum(1 for r in rooms.values() if r.get('items'))}")
    print(f"   Total Items: {sum(len(r.get('items', [])) for r in rooms.values())}")
    print(f"   Total Exits: {sum(len(r.get('exits', {})) for r in rooms.values())}")
    
    print()
    print("🔗 Connection Map:")
    for room_id, room in rooms.items():
        exits = room.get('exits', {})
        if exits:
            connections = [f"{direction}→{target}" for direction, target in exits.items()]
            print(f"   {room['name']}: {', '.join(connections)}")
    
    print()
    print("📦 Items by Room:")
    for room_id, room in rooms.items():
        items = room.get('items', [])
        if items:
            print(f"   {room['name']}: {', '.join(items)}")
        else:
            print(f"   {room['name']}: (no items)")

if __name__ == "__main__":
    generate_map()
