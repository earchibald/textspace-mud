# Database Migration and Deployment Guide

This guide explains how to migrate your Multi-User Text Space System from flat files to a database backend and deploy it in production.

## Overview

The system now supports two backends:
- **Flat File Backend**: Original YAML/JSON files (development/simple deployments)
- **Database Backend**: MongoDB + Redis (production/scalable deployments)

## Prerequisites

### For Database Backend

1. **MongoDB** (version 4.4+)
2. **Redis** (version 6.0+)
3. **Python Dependencies**:
   ```bash
   pip install pymongo redis bcrypt python-dotenv
   ```

### Installation Options

#### Option 1: Local Installation

**MongoDB:**
```bash
# macOS with Homebrew
brew install mongodb-community
brew services start mongodb-community

# Ubuntu/Debian
sudo apt-get install mongodb
sudo systemctl start mongodb

# Windows
# Download from https://www.mongodb.com/try/download/community
```

**Redis:**
```bash
# macOS with Homebrew
brew install redis
brew services start redis

# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis

# Windows
# Download from https://redis.io/download
```

#### Option 2: Docker Compose

Create `docker-compose.yml`:
```yaml
version: '3.8'
services:
  mongodb:
    image: mongo:5.0
    ports:
      - "27017:27017"
    environment:
      MONGO_INITDB_ROOT_USERNAME: textspace
      MONGO_INITDB_ROOT_PASSWORD: textspace123
    volumes:
      - mongodb_data:/data/db

  redis:
    image: redis:6.2-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  mongodb_data:
  redis_data:
```

Start with: `docker-compose up -d`

## Configuration

### Environment Variables

Create `.env` file:
```bash
# Database Configuration
USE_DATABASE=true
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=textspace
REDIS_URL=redis://localhost:6379
REDIS_DB=0

# Authentication
SECRET_KEY=your-secret-key-here
PASSWORD_SALT_ROUNDS=12

# Optional: MongoDB Authentication
# MONGODB_USERNAME=textspace
# MONGODB_PASSWORD=textspace123

# Optional: Redis Authentication
# REDIS_PASSWORD=your-redis-password
```

For Docker setup with authentication:
```bash
USE_DATABASE=true
MONGODB_URL=mongodb://textspace:textspace123@localhost:27017
MONGODB_DATABASE=textspace
REDIS_URL=redis://localhost:6379
SECRET_KEY=your-secret-key-here
```

## Migration Process

### Step 1: Backup Current System

The migration tool automatically creates backups, but you can also manually backup:
```bash
# Create backup directory
mkdir backup_manual
cp users.json rooms.yaml bots.yaml items.yaml scripts.yaml backup_manual/
```

### Step 2: Test Database Connection

```bash
# Test if databases are accessible
python -c "
import pymongo
import redis
print('Testing MongoDB...')
client = pymongo.MongoClient('mongodb://localhost:27017')
client.admin.command('ping')
print('MongoDB: OK')

print('Testing Redis...')
r = redis.Redis(host='localhost', port=6379, db=0)
r.ping()
print('Redis: OK')
"
```

### Step 3: Run Migration

```bash
# Full migration with backup
python migrate_v2.py migrate

# Migration without backup (if you already have one)
python migrate_v2.py migrate --no-backup

# Verify migration was successful
python migrate_v2.py verify
```

### Step 4: Update Configuration

```bash
# Set database mode in .env
echo "USE_DATABASE=true" >> .env
```

### Step 5: Test New System

```bash
# Start the enhanced server
python server_v2.py

# In another terminal, test connection
nc localhost 8888
# Or visit http://localhost:5000
```

## Deployment Strategies

### Strategy 1: Direct Migration (Downtime Required)

1. Stop current server
2. Run migration
3. Update configuration
4. Start new server

**Pros:** Simple, clean cutover
**Cons:** Service downtime during migration

### Strategy 2: Parallel Operation (Zero Downtime)

1. Set up database alongside flat files
2. Run parallel sync to keep database updated
3. Switch traffic to database backend
4. Decommission flat file system

**Implementation:**
```bash
# Terminal 1: Start parallel sync
python migrate_v2.py sync

# Terminal 2: Continue running old server
python server.py

# Terminal 3: Test new server (different ports)
USE_DATABASE=true python server_v2.py
```

### Strategy 3: Blue-Green Deployment

1. Set up complete new environment with database
2. Migrate data to new environment
3. Switch DNS/load balancer to new environment
4. Keep old environment as rollback option

## User Authentication Changes

### Default Passwords

After migration, users get default passwords:
- Format: `{username}123`
- Example: User "alice" gets password "alice123"

### Password Management

Users should change their passwords:
```bash
# Future feature - password change command
# /password old_password new_password
```

### Admin Users

- Admin status is preserved during migration
- Username "admin" retains admin privileges
- Additional admins can be promoted in database

## Monitoring and Maintenance

### Health Checks

```bash
# Check database connections
python -c "
from database import DatabaseManager
db = DatabaseManager()
print('Database health:', db.test_connections())
"

# Check data integrity
python migrate_v2.py verify
```

### Backup Procedures

```bash
# MongoDB backup
mongodump --db textspace --out backup_$(date +%Y%m%d)

# Redis backup
redis-cli BGSAVE
cp /var/lib/redis/dump.rdb backup_redis_$(date +%Y%m%d).rdb
```

### Log Monitoring

```bash
# Monitor server logs
tail -f textspace.log

# Monitor database logs
# MongoDB: /var/log/mongodb/mongod.log
# Redis: /var/log/redis/redis-server.log
```

## Performance Optimization

### MongoDB Indexes

```javascript
// Connect to MongoDB shell
use textspace

// Create indexes for better performance
db.users.createIndex({ "name": 1 }, { unique: true })
db.users.createIndex({ "last_seen": -1 })
db.rooms.createIndex({ "_id": 1 })
db.items.createIndex({ "_id": 1 })
db.items.createIndex({ "tags": 1 })
```

### Redis Configuration

```bash
# Add to redis.conf for persistence
save 900 1
save 300 10
save 60 10000
```

### Connection Pooling

The system uses connection pooling by default:
- MongoDB: 10-100 connections
- Redis: 10 connections

## Troubleshooting

### Common Issues

**1. Database Connection Failed**
```bash
# Check if services are running
brew services list | grep mongo
brew services list | grep redis

# Check ports
netstat -an | grep 27017  # MongoDB
netstat -an | grep 6379   # Redis
```

**2. Migration Fails**
```bash
# Check file permissions
ls -la *.yaml *.json

# Check database permissions
python -c "
from database import DatabaseManager
db = DatabaseManager()
try:
    db.users.insert_one({'test': 'data'})
    db.users.delete_one({'test': 'data'})
    print('Database write permissions: OK')
except Exception as e:
    print('Database write error:', e)
"
```

**3. Authentication Issues**
```bash
# Reset user password
python -c "
from auth import AuthenticationService
from database import DatabaseManager
auth = AuthenticationService(DatabaseManager())
auth.update_password('username', 'newpassword')
print('Password updated')
"
```

**4. Performance Issues**
```bash
# Check database stats
python -c "
from database import DatabaseManager
db = DatabaseManager()
print('Users:', db.users.count_documents({}))
print('Rooms:', db.rooms.count_documents({}))
print('Items:', db.items.count_documents({}))
"
```

### Rollback Procedure

If you need to rollback to flat files:

1. Stop database server
2. Restore from backup
3. Update .env: `USE_DATABASE=false`
4. Start original server: `python server.py`

## Production Deployment

### Security Considerations

1. **Database Security:**
   - Enable MongoDB authentication
   - Use Redis AUTH
   - Configure firewall rules
   - Use TLS/SSL for connections

2. **Application Security:**
   - Change default SECRET_KEY
   - Use strong password policies
   - Enable rate limiting
   - Monitor for suspicious activity

3. **Network Security:**
   - Run databases on private networks
   - Use VPN for remote access
   - Configure proper firewall rules

### Scaling Considerations

1. **Horizontal Scaling:**
   - MongoDB replica sets
   - Redis clustering
   - Load balancer for multiple server instances

2. **Vertical Scaling:**
   - Increase server resources
   - Optimize database queries
   - Use caching strategies

### Monitoring Setup

1. **Application Monitoring:**
   - Log aggregation (ELK stack)
   - Metrics collection (Prometheus)
   - Alerting (PagerDuty, Slack)

2. **Database Monitoring:**
   - MongoDB Compass
   - Redis monitoring tools
   - Custom health checks

## Migration Checklist

- [ ] Install MongoDB and Redis
- [ ] Install Python dependencies
- [ ] Create .env configuration
- [ ] Test database connections
- [ ] Create backup of flat files
- [ ] Run migration tool
- [ ] Verify migration success
- [ ] Update USE_DATABASE setting
- [ ] Test new server functionality
- [ ] Update user passwords
- [ ] Set up monitoring
- [ ] Configure backups
- [ ] Document rollback procedure

## Support

For issues during migration or deployment:

1. Check logs in `textspace.log`
2. Verify database connections
3. Run migration verification
4. Check file permissions
5. Review environment variables

The system is designed to be backward compatible, so you can always rollback to flat files if needed.
