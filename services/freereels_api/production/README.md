# FreeReels API Client - Production Deployment

**Version:** 1.4.0  
**Status:** Production-Ready for miniPC/Server Deployment

## 📦 Structure

```
production/
├── core/                    # Core client & auth
│   ├── __init__.py
│   ├── client.py           # Main FreeReelsClient
│   └── auth.py             # OAuth signing
├── api/                    # API Proxy Server
│   ├── proxy.py            # FastAPI server with playground
├── config/                 # Configuration
│   ├── settings.py         # API endpoints, languages, defaults
├── docs/                   # Documentation
│   ├── CHANGELOG.txt       # Version history
├── scripts/                # Utility scripts (optional)
├── requirements.txt        # Python dependencies
├── run_proxy.py            # Quick start script
└── README.md              # This file
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run API Proxy Server
```bash
python run_proxy.py
```

Server berjalan di **http://localhost:8000**

### 3. Access Playground
Buka browser: **http://localhost:8000/**

Fitur:
- 7 kategori drama (Popular, Female, Male, New, Dubbing, Anime, Coming Soon)
- 5 search endpoints (Hot Words, Trending, Audio Tabs, Search Drama, Suggestions)
- Custom endpoint `/api/tabs/complete` dengan anime injected
- Drama detail, history, following
- Profile & wallet info

## 📡 API Endpoints (Proxy)

### Categories
- `GET /homepage/v2/tab/index?tab_key=503&position_index=0` - Populer
- `GET /homepage/v2/tab/index?tab_key=504&position_index=0` - Perempuan (Female)
- `GET /homepage/v2/tab/index?tab_key=505&position_index=0` - New
- `GET /homepage/v2/tab/index?tab_key=506&position_index=0` - Laki-Laki (Male)
- `GET /homepage/v2/tab/index?tab_key=516&position_index=0` - Dubbing
- `GET /homepage/v2/tab/index?tab_key=547&position_index=0` - Anime
- `GET /homepage/v2/tab/index?tab_key=622&position_index=0` - Segera Hadir (Coming Soon)

### Search
- `GET /search/hot_words` - Hot keywords
- `GET /search/trending_searches` - Trending
- `GET /search/audio-tabs` - Audio dubbing filters
- `POST /search/drama` - Search by keyword
- `POST /search/suggestion` - Auto-complete

### Custom
- `GET /api/tabs/complete` - Tab list dengan anime (547) injected

## 🔑 Key Features

✅ **Anonymous Login** - No credentials required  
✅ **Multi-Language** - 22 verified languages  
✅ **AES Decryption** - Auto-decrypt responses from libdwguard.so keys  
✅ **Pagination** - All categories support pagination via `position_index`  
✅ **Gender Filter** - Female (504) & Male (506) categories  
✅ **Hidden Anime** - Anime (547) discovered but not in official tab list  
✅ **Web Playground** - Interactive testing UI at root endpoint

## ⚙️ Configuration

Edit `config/settings.py` untuk:
- API endpoints
- Language defaults
- Proxy server settings
- AES encryption keys

## 🌍 Supported Languages (22)

Indonesian, English, Spanish, Portuguese, French, German, Italian, Russian, Arabic, Hindi, Tamil, Telugu, Bengali, Thai, Vietnamese, Filipino, Malay, Japanese, Korean, Chinese, Polish, Turkish

Default: **Indonesian (id-ID)**

## 📝 Python Usage Example

```python
from core import FreeReelsClient

# Initialize client
client = FreeReelsClient()

# Anonymous login (no credentials needed)
client.login_anonymous()

# Get dramas from Popular category
dramas = client.get_dramas_by_category("503")
print(f"Found {len(dramas)} dramas")

# Get female-oriented dramas
female_dramas = client.get_dramas_by_category("504")

# Search dramas
results = client.search_drama("love")

# Get all tabs with anime injected
tabs = client.get_homepage_tabs()
```

## 🔧 Troubleshooting

### Server won't start on port 8000
```bash
# Check if port is in use
netstat -ano | findstr :8000

# Kill process if needed
taskkill /PID <PID> /F

# Or use different port - edit run_proxy.py
```

### "401 Authentication failed"
- Anonymous login endpoint might be rate-limited
- Wait 30 seconds and try again
- Check internet connection

### "x-decry header not found"
- Some endpoints don't need decryption
- Response is already JSON

## 📊 Deployment to miniPC

1. Copy entire `production/` folder to miniPC
2. Install Python 3.8+
3. Run: `pip install -r requirements.txt`
4. Run: `python run_proxy.py`
5. Access from other machines: `http://<minipc-ip>:8000`

## 📄 Changelog

See `docs/CHANGELOG.txt` for version history.

---

**Last Updated:** 2026-10-04  
**Version:** 1.4.0 (Production Ready)
