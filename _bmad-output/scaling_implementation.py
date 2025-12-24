"""
TextSpace Scaling Implementation - Stage 1 Enhancements
Minimal code additions for immediate scaling improvements
"""

# Redis connection pool for room state management
import redis
from redis.connection import ConnectionPool

class ScalableRoomManager:
    def __init__(self):
        self.pool = ConnectionPool(host='localhost', port=6379, db=0, max_connections=20)
        self.redis_client = redis.Redis(connection_pool=self.pool)
    
    def get_room_state(self, room_id):
        """Get room state from Redis with fallback to memory"""
        cached = self.redis_client.hgetall(f"room:{room_id}")
        return {k.decode(): v.decode() for k, v in cached.items()} if cached else {}
    
    def update_room_state(self, room_id, state_data):
        """Update room state in Redis"""
        self.redis_client.hmset(f"room:{room_id}", state_data)
        self.redis_client.expire(f"room:{room_id}", 3600)  # 1 hour TTL

# Message broadcasting optimization
class OptimizedBroadcaster:
    def __init__(self, socketio):
        self.socketio = socketio
        self.room_connections = {}
    
    def broadcast_to_room(self, room_id, message, exclude_sid=None):
        """Optimized room broadcasting"""
        if room_id in self.room_connections:
            for sid in self.room_connections[room_id]:
                if sid != exclude_sid:
                    self.socketio.emit('message', message, room=sid)

# Connection pooling for WebSocket management
class ConnectionManager:
    def __init__(self):
        self.active_connections = {}
        self.room_assignments = {}
    
    def add_connection(self, sid, room_id):
        self.active_connections[sid] = {'room': room_id, 'last_ping': datetime.now()}
        if room_id not in self.room_assignments:
            self.room_assignments[room_id] = set()
        self.room_assignments[room_id].add(sid)
    
    def remove_connection(self, sid):
        if sid in self.active_connections:
            room_id = self.active_connections[sid]['room']
            self.room_assignments[room_id].discard(sid)
            del self.active_connections[sid]
