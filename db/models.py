"""
Database models and schemas
"""
from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime

@dataclass
class User:
    name: str
    room_id: str = "lobby"
    inventory: List[str] = None
    admin: bool = False
    password_hash: Optional[str] = None
    session_id: Optional[str] = None
    last_seen: Optional[datetime] = None
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.inventory is None:
            self.inventory = []
        if self.created_at is None:
            self.created_at = datetime.utcnow()

@dataclass
class Room:
    id: str
    name: str
    description: str
    exits: Dict[str, str] = None
    items: List[str] = None
    
    def __post_init__(self):
        if self.exits is None:
            self.exits = {}
        if self.items is None:
            self.items = []

@dataclass
class Item:
    id: str
    name: str
    description: str
    tags: List[str] = None
    is_container: bool = False
    contents: List[str] = None
    script: Optional[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.contents is None:
            self.contents = []

@dataclass
class Bot:
    id: str
    name: str
    room_id: str
    description: str
    responses: List[Dict] = None
    visible: bool = True
    inventory: List[str] = None
    
    def __post_init__(self):
        if self.responses is None:
            self.responses = []
        if self.inventory is None:
            self.inventory = []
