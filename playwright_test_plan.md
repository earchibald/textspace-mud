# Playwright MCP Test Plan for The Text Spot v2.0.1

## Test Target
- **URL**: https://exciting-liberation-production.up.railway.app
- **Version**: 2.0.1 (Web-Only)
- **Testing Tool**: Playwright MCP via Kiro CLI

## Functional Requirements to Test

### FR-01: Server Initialization & Web Interface
- [ ] Page loads successfully
- [ ] Title shows "The Text Spot"
- [ ] Header shows "The Text Spot"
- [ ] Input box is present and focused
- [ ] Connection status shows connected

### FR-02: Version Tracking
- [ ] Login as user
- [ ] Type 'version' command
- [ ] Verify response shows "The Text Spot v2.0.1"
- [ ] Test 'v' alias works

### FR-03: Command Aliases
- [ ] Test single-letter aliases: n, s, e, w, l, g, i, h, v
- [ ] Test quote alias: "Hello everyone!
- [ ] Verify aliases produce same results as full commands

### FR-04: Room Navigation
- [ ] Test exact matching: 'go greenhouse'
- [ ] Test partial matching: 'go green' → greenhouse
- [ ] Test ambiguous matching shows options
- [ ] Test cardinal directions: n, s, e, w

### FR-05: User Authentication
- [ ] Login as regular user - no admin commands in help
- [ ] Login as 'admin' - admin commands shown
- [ ] Test admin privileges work

### FR-06: Help System
- [ ] Type 'help' shows basic commands with aliases
- [ ] Admin help shows admin commands section
- [ ] Version command listed in help

### FR-07: Communication Commands
- [ ] Test 'say' command
- [ ] Test quote alias '"' for say
- [ ] Test 'whisper' command
- [ ] Test 'who' command shows users

### FR-08: Inventory & Items
- [ ] Test 'inventory' command
- [ ] Test 'i' alias for inventory
- [ ] Test item interactions if available

### FR-09: Auto-Login & User Switching
- [ ] Test localStorage auto-login
- [ ] Test switchuser command (admin only)

### FR-10: Admin Commands
- [ ] Test 'teleport' command
- [ ] Test 'broadcast' command  
- [ ] Test 'kick' command
- [ ] Test 'switchuser' command

## Test Execution Plan

1. **Initialize Browser & Navigate**
2. **Test Basic Functionality**
3. **Test User Authentication**
4. **Test Command System**
5. **Test Admin Features**
6. **Test Auto-Login**
7. **Generate Test Report**

## Expected Outcomes

- All functional requirements pass
- No JavaScript errors in console
- Proper WebSocket connectivity
- Commands execute and return expected responses
- UI remains responsive throughout testing

## Test Data Collection

- Screenshots of key interactions
- Console logs for debugging
- Response times for commands
- Error messages (if any)
- Feature compatibility matrix
