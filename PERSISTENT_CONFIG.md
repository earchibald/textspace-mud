# TextSpace Persistent Configuration System

## 🎯 **Overview**

The TextSpace server now uses a **persistent configuration system** that separates live server config from repository code, ensuring configuration survives deployments and provides safe reset mechanisms.

## 🏗️ **Architecture**

### **Before (Problems)**
```
Git Repo → Railway Deploy → Config Files Overwritten ❌
```

### **After (Solution)**
```
Git Repo (Examples) → Railway Deploy → Persistent Volume → Live Config ✅
```

## 📁 **File Structure**

```
TextSpace Repository:
├── config_examples/          # Example configurations (in Git)
│   ├── rooms.yaml            # Default room layout
│   ├── bots.yaml             # Default bot configurations  
│   ├── items.yaml            # Default item definitions
│   └── scripts.yaml          # Default bot scripts
├── config_manager.py         # Configuration management system
├── start_railway.sh          # Railway startup script
└── server_web_only.py        # Updated server with config manager

Railway Persistent Volume:
├── /app/data/                # Persistent configuration storage
│   ├── rooms.yaml            # Live room configuration
│   ├── bots.yaml             # Live bot configuration
│   ├── items.yaml            # Live item configuration
│   ├── scripts.yaml          # Live script configuration
│   └── *.backup.*            # Automatic backups
```

## 🔧 **How It Works**

### **1. Initialization (First Deploy)**
```bash
# Railway startup process:
1. start_railway.sh runs
2. config_manager.py init
3. Copies config_examples/ → /app/data/
4. Creates symlinks: rooms.yaml → /app/data/rooms.yaml
5. Server starts with persistent config
```

### **2. Configuration Updates (Via MCP)**
```bash
# MCP Server → Railway API → Persistent Storage
1. MCP tool: write_config
2. HTTPS POST /api/config/rooms
3. Writes to /app/data/rooms.yaml
4. Creates backup: rooms.yaml.backup.20251221_183000
5. Server reloads: load_data()
6. Config persists through deployments ✅
```

### **3. Safe Reset System**
```bash
# Double confirmation required:
1. reset_config rooms (no code)
   → Returns: "Required code: RESET_ROOMS_20251221"
2. reset_config rooms RESET_ROOMS_20251221
   → Creates backup + resets to example
```

## 🛠️ **MCP Server Updates**

### **New Tools Added**

#### `config_info`
Get information about configuration storage:
```json
{
  "persistent_path": "/app/data",
  "example_path": "./config_examples", 
  "configs": {
    "rooms": {
      "persistent_exists": true,
      "persistent_size": 1165,
      "example_exists": true,
      "last_modified": 1703187600
    }
  }
}
```

#### `reset_config`
Reset configuration with double confirmation:
```bash
# Step 1: Get confirmation code
reset_config rooms
# Returns: "Required code: RESET_ROOMS_20251221"

# Step 2: Confirm reset
reset_config rooms RESET_ROOMS_20251221
# Returns: "Config reset successful, backup created"
```

### **Enhanced API Endpoints**

#### `POST /api/config/reset/<type>`
```json
{
  "confirmation_code": "RESET_ROOMS_20251221"
}
```

#### `GET /api/config/info`
Returns configuration storage information.

## 🚀 **Deployment Process**

### **Railway Configuration**
- **Startup Command**: `./start_railway.sh`
- **Persistent Volume**: `/app/data` (Railway managed)
- **Environment Detection**: `RAILWAY_ENVIRONMENT` variable

### **Deployment Flow**
```bash
1. Git push → Railway detects changes
2. Railway builds new container
3. start_railway.sh initializes config (if needed)
4. Server starts with persistent config
5. Live config unchanged ✅
```

## 🔒 **Safety Features**

### **Automatic Backups**
- Every config write creates timestamped backup
- Format: `rooms.yaml.backup.20251221_183000`
- Stored in persistent volume
- Never lost during deployments

### **Double Confirmation Reset**
- Daily-changing confirmation codes
- Format: `RESET_{TYPE}_{YYYYMMDD}`
- Prevents accidental resets
- Creates backup before reset

### **Example Config Maintenance**
- Examples stay in Git repository
- Updated with `config_manager.py update-examples`
- Provides clean reset target
- Version controlled defaults

## 📋 **Usage Examples**

### **Via MCP Tools**

#### Check Configuration Status
```python
info = await call_tool("config_info", {})
# Shows persistent storage status
```

#### Update Live Configuration
```python
# Read current config
config = await call_tool("read_config", {"config_type": "rooms"})

# Modify and write back
result = await call_tool("write_config", {
    "config_type": "rooms",
    "content": modified_yaml
})
# Creates backup, updates persistent storage
```

#### Safe Configuration Reset
```python
# Step 1: Get confirmation code
result = await call_tool("reset_config", {"config_type": "rooms"})
# Returns required confirmation code

# Step 2: Confirm reset
result = await call_tool("reset_config", {
    "config_type": "rooms", 
    "confirmation_code": "RESET_ROOMS_20251221"
})
# Resets to example, creates backup
```

### **Via Direct API**

#### Get Configuration Info
```bash
curl https://textspace-mud-production.up.railway.app/api/config/info
```

#### Reset Configuration
```bash
# Get confirmation code
curl -X POST https://textspace-mud-production.up.railway.app/api/config/reset/rooms \
  -H "Content-Type: application/json" \
  -d '{}'

# Confirm reset
curl -X POST https://textspace-mud-production.up.railway.app/api/config/reset/rooms \
  -H "Content-Type: application/json" \
  -d '{"confirmation_code": "RESET_ROOMS_20251221"}'
```

## 🔄 **Migration Process**

### **Current State → New System**
```bash
1. Deploy new system (automatic)
2. Railway initializes persistent config from examples
3. Live config now persistent ✅
4. Future deployments preserve config ✅
```

### **No Manual Migration Required**
- System automatically handles first-time setup
- Existing config becomes persistent
- No downtime or data loss

## ⚠️ **Important Changes**

### **For Developers**
- ✅ **Config Examples**: Edit `config_examples/` for defaults
- ✅ **Live Config**: Use MCP tools for server changes
- ❌ **Direct Edit**: Don't edit root `*.yaml` files (they're symlinks)

### **For Admins**
- ✅ **Persistent Changes**: All MCP config changes survive deployments
- ✅ **Safe Resets**: Double confirmation prevents accidents
- ✅ **Automatic Backups**: Every change creates backup
- ⚠️ **Reset Codes**: Change daily for security

## 🎯 **Benefits**

### **Operational**
- ✅ **Config Survives Deployments**: No more lost configurations
- ✅ **Safe Reset Mechanism**: Double confirmation prevents accidents
- ✅ **Automatic Backups**: Every change creates timestamped backup
- ✅ **Clean Separation**: Examples vs live config clearly separated

### **Development**
- ✅ **Version Controlled Examples**: Default configs in Git
- ✅ **No Config Conflicts**: Live config not in repository
- ✅ **Easy Testing**: Reset to known good state
- ✅ **Deployment Safety**: Can't accidentally overwrite live config

### **Management**
- ✅ **Remote Configuration**: Full CRUD via MCP tools
- ✅ **Configuration Tracking**: Backup history and timestamps
- ✅ **Status Monitoring**: Config info API shows storage status
- ✅ **Disaster Recovery**: Reset to examples when needed

---

**Version**: 2.0.21+  
**Status**: ✅ PRODUCTION READY  
**Persistent Storage**: ✅ RAILWAY VOLUME INTEGRATED
