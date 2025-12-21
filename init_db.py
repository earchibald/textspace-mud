#!/usr/bin/env python
"""
Initialize database with YAML configuration data
Run this once after deployment to populate the database
"""
import asyncio
from db import Database, Room, Item, Bot

async def init_database():
    import yaml
    
    db = Database()
    print("Initializing database...")
    
    # Load and save rooms
    with open('rooms.yaml', 'r') as f:
        rooms_data = yaml.safe_load(f)
        for room_id, room_data in rooms_data['rooms'].items():
            room = Room(
                id=room_id,
                name=room_data['name'],
                description=room_data['description'],
                exits=room_data.get('exits', {}),
                items=room_data.get('items', [])
            )
            db.save_room(room)
            print(f"  Saved room: {room_id}")
    
    # Load and save items
    with open('items.yaml', 'r') as f:
        items_data = yaml.safe_load(f)
        for item_id, item_data in items_data['items'].items():
            item = Item(
                id=item_id,
                name=item_data['name'],
                description=item_data['description'],
                tags=item_data.get('tags', []),
                is_container=item_data.get('is_container', False),
                contents=item_data.get('contents', []),
                script=item_data.get('script')
            )
            db.save_item(item)
            print(f"  Saved item: {item_id}")
    
    # Load and save bots
    with open('bots.yaml', 'r') as f:
        bots_data = yaml.safe_load(f)
        for bot_id, bot_data in bots_data['bots'].items():
            bot = Bot(
                id=bot_id,
                name=bot_data['name'],
                room_id=bot_data['room'],
                description=bot_data['description'],
                responses=bot_data.get('responses', []),
                visible=bot_data.get('visible', True),
                inventory=bot_data.get('inventory', [])
            )
            db.save_bot(bot)
            print(f"  Saved bot: {bot_id}")
    
    print("✅ Database initialized successfully!")

if __name__ == "__main__":
    asyncio.run(init_database())
