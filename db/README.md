# Database Module

This module provides database abstraction for the Multi-User Text Space System.

## Components

- `__init__.py` - Module initialization and main interface
- `sqlite_backend.py` - SQLite database implementation
- `models.py` - Data models and schemas

## Usage

```python
from db import Database

# Initialize database
db = Database()

# Use database operations
users = db.get_all_users()
db.save_user(user_data)
```
