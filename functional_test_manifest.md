# Functional Testing Manifest - The Text Spot v2.0.2
**Target**: https://exciting-liberation-production.up.railway.app  
**Test Date**: 2025-12-21  
**Scope**: Complete user interface and functionality testing

## Test Categories

### 1. CONNECTION & AUTHENTICATION
- [ ] Page loads successfully
- [ ] WebSocket connection established
- [ ] Login with regular username
- [ ] Login with admin username
- [ ] Auto-login from localStorage
- [ ] Multiple user sessions

### 2. COMMAND PARSING & ALIASES
- [ ] Single-letter aliases: w, n, s, e, l, g, i, h, v
- [ ] Partial matching: wh → ambiguous, whi → whisper
- [ ] Exact commands work
- [ ] Ambiguous command handling
- [ ] Quote alias for say: "message

### 3. BASIC NAVIGATION
- [ ] look/l command shows room details
- [ ] Cardinal directions: north, south, east, west
- [ ] go command with room names
- [ ] Partial room name matching
- [ ] Invalid direction handling

### 4. COMMUNICATION
- [ ] say command broadcasts to room
- [ ] Quote alias "message works
- [ ] whisper command private messaging
- [ ] who command lists users
- [ ] Player enter/leave notifications

### 5. INVENTORY & ITEMS
- [ ] inventory/i command
- [ ] get/take item from room
- [ ] drop item to room
- [ ] examine item details
- [ ] use item functionality

### 6. ADMIN COMMANDS
- [ ] teleport to different rooms
- [ ] broadcast message to all users
- [ ] kick user functionality
- [ ] switchuser command
- [ ] Admin-only command restrictions

### 7. ROOM SYSTEM
- [ ] Room descriptions include all elements
- [ ] Exits displayed correctly
- [ ] Users in room shown
- [ ] Bots in room shown
- [ ] Items in room shown
- [ ] Room persistence

### 8. ERROR HANDLING
- [ ] Unknown commands
- [ ] Invalid arguments
- [ ] Non-existent rooms/users/items
- [ ] Permission denied messages
- [ ] Connection loss recovery

### 9. MULTI-USER INTERACTION
- [ ] Multiple users in same room
- [ ] Real-time message updates
- [ ] User movement notifications
- [ ] Concurrent command execution

### 10. VERSION & HELP
- [ ] version/v command shows v2.0.2
- [ ] help/h shows all commands
- [ ] Admin help shows admin commands
- [ ] Command syntax examples

## Test Execution Protocol

Each test will be performed with specific inputs and expected outputs documented.
Pass/Fail status will be recorded with detailed observations.
