#!/usr/bin/env python3
"""
TextSpace Room Map Visual Generator
Creates visual map as PNG and PDF
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch
import numpy as np

def create_visual_map():
    """Create visual map of TextSpace rooms"""
    
    # Create figure and axis
    fig, ax = plt.subplots(1, 1, figsize=(16, 12))
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 12)
    ax.set_aspect('equal')
    
    # Define room positions and sizes
    rooms = {
        'greenhouse': {'pos': (7, 10), 'size': (2.5, 1.5), 'color': '#90EE90', 'emoji': '🌿'},
        'garden': {'pos': (7, 8), 'size': (2.5, 1.5), 'color': '#FFB6C1', 'emoji': '🌸'},
        'library': {'pos': (2, 5.5), 'size': (2.5, 1.5), 'color': '#DDA0DD', 'emoji': '📚'},
        'lobby': {'pos': (7, 5.5), 'size': (2.5, 1.5), 'color': '#F0E68C', 'emoji': '🏛️'},
        'mcp_test': {'pos': (12, 5.5), 'size': (2.5, 1.5), 'color': '#87CEEB', 'emoji': '🧪'},
        'study': {'pos': (2, 3), 'size': (2.5, 1.5), 'color': '#DEB887', 'emoji': '📖'},
        'playground': {'pos': (7, 3), 'size': (2.5, 1.5), 'color': '#FFA07A', 'emoji': '🎮'}
    }
    
    # Room details
    room_info = {
        'greenhouse': {'name': 'Greenhouse', 'desc': 'Plants & Butterflies', 'items': []},
        'garden': {'name': 'Garden', 'desc': 'Flowers & Fountain', 'items': ['flower_seeds']},
        'library': {'name': 'Library', 'desc': 'Books & Reading', 'items': ['magic_book', 'story_scroll']},
        'lobby': {'name': 'Lobby', 'desc': 'Entrance Hall', 'items': ['treasure_chest']},
        'mcp_test': {'name': 'MCP Test Room', 'desc': 'Testing Space', 'items': []},
        'study': {'name': 'Study Room', 'desc': 'Desks & Learning', 'items': []},
        'playground': {'name': 'Playground', 'desc': 'Toys & Games', 'items': []}
    }
    
    # Draw rooms
    for room_id, room in rooms.items():
        x, y = room['pos']
        w, h = room['size']
        
        # Create fancy room box
        fancy_box = FancyBboxPatch(
            (x - w/2, y - h/2), w, h,
            boxstyle="round,pad=0.1",
            facecolor=room['color'],
            edgecolor='black',
            linewidth=2
        )
        ax.add_patch(fancy_box)
        
        # Add room emoji
        ax.text(x, y + 0.3, room['emoji'], fontsize=20, ha='center', va='center')
        
        # Add room name
        ax.text(x, y, room_info[room_id]['name'], fontsize=12, ha='center', va='center', weight='bold')
        
        # Add description
        ax.text(x, y - 0.2, room_info[room_id]['desc'], fontsize=9, ha='center', va='center', style='italic')
        
        # Add items if any
        items = room_info[room_id]['items']
        if items:
            items_text = f"[{', '.join(items)}]"
            ax.text(x, y - 0.5, items_text, fontsize=8, ha='center', va='center', color='darkgreen')
    
    # Define connections
    connections = [
        ('garden', 'greenhouse', 'north'),
        ('garden', 'lobby', 'south'),
        ('library', 'lobby', 'east'),
        ('library', 'study', 'south'),
        ('lobby', 'playground', 'south'),
        ('mcp_test', 'lobby', 'west')
    ]
    
    # Draw connections
    for room1, room2, direction in connections:
        x1, y1 = rooms[room1]['pos']
        x2, y2 = rooms[room2]['pos']
        
        # Calculate connection points
        if direction == 'north':
            start = (x1, y1 + rooms[room1]['size'][1]/2)
            end = (x2, y2 - rooms[room2]['size'][1]/2)
        elif direction == 'south':
            start = (x1, y1 - rooms[room1]['size'][1]/2)
            end = (x2, y2 + rooms[room2]['size'][1]/2)
        elif direction == 'east':
            start = (x1 + rooms[room1]['size'][0]/2, y1)
            end = (x2 - rooms[room2]['size'][0]/2, y2)
        elif direction == 'west':
            start = (x1 - rooms[room1]['size'][0]/2, y1)
            end = (x2 + rooms[room2]['size'][0]/2, y2)
        
        # Draw arrow
        ax.annotate('', xy=end, xytext=start,
                   arrowprops=dict(arrowstyle='<->', color='darkblue', lw=2))
    
    # Add title and info
    ax.text(8, 11.5, '🗺️ TextSpace Room Map', fontsize=24, ha='center', weight='bold')
    
    # Add statistics box
    stats_text = """📊 Statistics:
• Total Rooms: 7
• Rooms with Items: 3
• Total Items: 4
• Total Connections: 6"""
    
    ax.text(0.5, 11, stats_text, fontsize=10, ha='left', va='top',
           bbox=dict(boxstyle="round,pad=0.5", facecolor='lightgray', alpha=0.8))
    
    # Add legend
    legend_text = """🎨 Room Types:
🌿 Nature Areas    📚 Learning Spaces
🏛️ Central Hub     🧪 Test Areas
🎮 Recreation      📖 Study Areas"""
    
    ax.text(15.5, 11, legend_text, fontsize=10, ha='right', va='top',
           bbox=dict(boxstyle="round,pad=0.5", facecolor='lightyellow', alpha=0.8))
    
    # Remove axes
    ax.set_xticks([])
    ax.set_yticks([])
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(False)
    
    # Save as PNG
    plt.tight_layout()
    plt.savefig('textspace_room_map.png', dpi=300, bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    print("✅ Saved as textspace_room_map.png")
    
    # Save as PDF
    plt.savefig('textspace_room_map.pdf', bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    print("✅ Saved as textspace_room_map.pdf")
    
    plt.close()

if __name__ == "__main__":
    create_visual_map()
    print("🎯 Visual map generation complete!")
