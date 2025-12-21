#!/usr/bin/env python3
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room
import yaml
from dataclasses import dataclass
from typing import Dict, Set

@dataclass
class Room:
    id: str
    name: str
    description: str
    exits: Dict[str, str]
    users: set = None
    
    def __post_init__(self):
        if self.users is None:
            self.users = set()

@dataclass
class WebUser:
    name: str
    session_id: str
    room_id: str = "lobby"

app = Flask(__name__)
app.config['SECRET_KEY'] = 'textspace-secret'
socketio = SocketIO(app, cors_allowed_origins="*")

class WebTextSpace:
    def __init__(self):
        self.users: Dict[str, WebUser] = {}
        self.sessions: Dict[str, str] = {}  # session_id -> username
        self.rooms: Dict[str, Room] = {}
        self.load_rooms()
    
    def load_rooms(self):
        try:
            with open('rooms.yaml', 'r') as f:
                data = yaml.safe_load(f)
                for room_id, room_data in data['rooms'].items():
                    self.rooms[room_id] = Room(
                        id=room_id,
                        name=room_data['name'],
                        description=room_data['description'],
                        exits=room_data.get('exits', {})
                    )
        except FileNotFoundError:
            self.rooms['lobby'] = Room(
                id='lobby',
                name='The Lobby',
                description='A simple starting room.',
                exits={}
            )

web_space = WebTextSpace()

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def on_connect():
    emit('message', {'text': 'Welcome to the Text Space! Enter your name:'})

@socketio.on('login')
def on_login(data):
    username = data['username'].strip()
    if not username or username in web_space.users:
        emit('message', {'text': 'Name taken or invalid. Try another:'})
        return
    
    user = WebUser(name=username, session_id=request.sid)
    web_space.users[username] = user
    web_space.sessions[request.sid] = username
    web_space.rooms[user.room_id].users.add(username)
    
    join_room(user.room_id)
    send_room_info(user)

@socketio.on('command')
def on_command(data):
    if request.sid not in web_space.sessions:
        emit('message', {'text': 'Please login first.'})
        return
    
    username = web_space.sessions[request.sid]
    user = web_space.users[username]
    command = data['command'].strip()
    
    if command.startswith('look'):
        send_room_info(user)
    elif command.startswith('say '):
        text = command[4:].strip()
        emit('message', {'text': f'You say: {text}'})
        socketio.emit('message', {'text': f'{username} says: {text}'}, 
                     room=user.room_id, include_self=False)
    elif command.startswith('go '):
        exit_name = command[3:].strip()
        move_user(user, exit_name)
    elif command in web_space.rooms[user.room_id].exits:
        move_user(user, command)
    elif command == 'who':
        users = ', '.join(web_space.users.keys())
        emit('message', {'text': f'Online users: {users}'})
    else:
        emit('message', {'text': f'Unknown command: {command}'})

def send_room_info(user):
    room = web_space.rooms[user.room_id]
    users_here = [name for name in room.users if name in web_space.users]
    others = [name for name in users_here if name != user.name]
    
    info = f"{room.name}\n{room.description}"
    
    if room.exits:
        exits = ", ".join(room.exits.keys())
        info += f"\nExits: {exits}"
    
    if others:
        info += f"\nOthers here: {', '.join(others)}"
    
    emit('room_info', {
        'name': room.name,
        'description': room.description,
        'exits': list(room.exits.keys()),
        'users': others
    })

def move_user(user, exit_name):
    current_room = web_space.rooms[user.room_id]
    
    if exit_name not in current_room.exits:
        emit('message', {'text': f"No exit '{exit_name}' here."})
        return
    
    new_room_id = current_room.exits[exit_name]
    if new_room_id not in web_space.rooms:
        emit('message', {'text': "Exit leads nowhere."})
        return
    
    # Move user
    leave_room(user.room_id)
    current_room.users.discard(user.name)
    user.room_id = new_room_id
    web_space.rooms[new_room_id].users.add(user.name)
    join_room(new_room_id)
    
    send_room_info(user)

@socketio.on('disconnect')
def on_disconnect():
    if request.sid in web_space.sessions:
        username = web_space.sessions[request.sid]
        if username in web_space.users:
            user = web_space.users[username]
            web_space.rooms[user.room_id].users.discard(username)
            del web_space.users[username]
        del web_space.sessions[request.sid]

if __name__ == '__main__':
    socketio.run(app, host='localhost', port=5000, debug=True)
