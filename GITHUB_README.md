🎮 **Multi-User Text Space System**

A social/community-focused multi-user text space system with educational features, real-time communication, scriptable bots, and interactive items.

## 🚀 **Quick Deploy to Railway**

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/textspace-mud)

## ✨ **Features**
- Real-time TCP and web interfaces
- Educational bots and interactive items  
- SQLite database with flat file fallback
- Comprehensive admin tools
- Zero-downtime migration system

## 📖 **Documentation**
See [README.md](README.md) for complete documentation.

## 🛠 **Local Development**
```bash
git clone https://github.com/earchibald/textspace-mud.git
cd textspace-mud
source venv/bin/activate
pip install -r requirements.txt -r requirements-db.txt
./server.py
```

Connect via: `nc localhost 8888` or `http://localhost:5000`
