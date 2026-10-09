# iQIYI Catalog & VIP Metadata REST API

Standalone Python FastAPI service exposing iQIYI International catalog metadata and authentication. Direct-client architecture with local JSON session persistence.

## Features

- **Authentication**: Login via phone/email and password with RSA-encrypted credentials
- **Search**: Paginated drama search with keyword support
- **Catalog**: Browse curated feeds, tabs, drama details, and episode listings
- **VIP Detection**: Track VIP account status and exclusive content availability
- **Session Management**: Local JSON persistence for session data

## Requirements

- Python 3.10+
- pip / virtualenv

## Installation

```bash
# Clone repository
cd "D:\BackEnd\Drama\iQIYI API"

# Create virtual environment
python -m venv venv
source venv/Scripts/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Configuration

Create `.env` file from template:

```bash
cp .env.example .env
```

Edit `.env`:

```env
IQIYI_USERNAME=your_phone_number_or_email
IQIYI_PASSWORD=your_password
SERVER_PORT=7407
SERVER_HOST=0.0.0.0
```

## Running the Server

```bash
python production/run_server.py
```

Server starts on `http://localhost:7407`

API documentation available at:
- Swagger UI: `http://localhost:7407/docs`
- ReDoc: `http://localhost:7407/redoc`

## API Endpoints

### Authentication

#### Login
```
POST /api/auth/login
Content-Type: application/json

{
  "username": "085161230944",
  "password": "your_password"
}

Response (200 OK):
{
  "code": 200,
  "message": "Login successful",
  "data": {
    "is_active": true,
    "vip_status": true,
    "account_identifier": "085161230944",
    "vip_type": "Premium VIP",
    "created_at": "2026-10-06T03:00:00Z"
  }
}
```

#### Check Session Status
```
GET /api/auth/status

Response (200 OK):
{
  "code": 200,
  "message": "Active session found",
  "data": {
    "is_active": true,
    "vip_status": true,
    "account_identifier": "085161230944",
    "vip_type": "Premium VIP",
    "created_at": "2026-10-06T03:00:00Z"
  }
}

Response (401 Unauthorized) if no active session
```

### Catalog

#### Search Dramas
```
POST /api/search
Content-Type: application/json

{
  "keyword": "cinta",
  "pg_num": 1
}

Response (200 OK):
{
  "code": 200,
  "message": "success",
  "data": {
    "keyword": "cinta",
    "pg_num": 1,
    "has_more": true,
    "items": [
      {
        "id": "12345",
        "name": "Love Story",
        "desc": "A romantic drama",
        "cover": "https://...",
        "genre": "Romance",
        "tags": ["love", "romance"],
        "year": 2024,
        "vip_status": false,
        "total_episodes": 16
      }
    ]
  }
}
```

#### Get Feed Items
```
GET /api/feed

Response (200 OK):
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "id": "feed_1",
      "name": "Trending Now",
      "cover": "https://...",
      "desc": "Popular series",
      "badge": "NEW",
      "is_vip": true
    }
  ]
}
```

#### Get Navigation Tabs
```
GET /api/tabs

Response (200 OK):
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "tab_key": "1036",
      "name": "Popular",
      "module_key": "popular_module"
    },
    {
      "tab_key": "1040",
      "name": "New Releases",
      "module_key": "new_module"
    }
  ]
}
```

#### Get Drama Details
```
GET /api/drama/{album_id}

Response (200 OK):
{
  "code": 200,
  "message": "success",
  "data": {
    "id": "12345",
    "name": "Love Story",
    "desc": "A romantic drama series",
    "cover": "https://...",
    "genre": "Romance",
    "tags": ["love"],
    "year": 2024,
    "vip_status": false,
    "total_episodes": 20
  }
}
```

#### Get Episode List
```
GET /api/drama/{album_id}/episodes

Response (200 OK):
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "episode_number": 1,
      "title": "Episode 1",
      "duration": 2400,
      "is_vip": false,
      "subtitles": ["en", "id"],
      "video_id": "vid_1"
    }
  ]
}
```

### Health Check

```
GET /health

Response (200 OK):
{
  "code": 200,
  "message": "OK",
  "data": {
    "status": "healthy"
  }
}
```

## Response Format

All endpoints return standardized JSON envelope:

```json
{
  "code": <http_status_code>,
  "message": "<status_message>",
  "data": <payload_or_null>
}
```

## Session Storage

Active session persisted to `data/sessions.json`:

```json
{
  "active_session": {
    "id": "uuid-string",
    "account_identifier": "085161230944",
    "auth_cookie": "QC005=...; P00001=...",
    "cookie_data": {"QC005": "...", "P00001": "..."},
    "device_id": "...",
    "vip_status": true,
    "vip_type": "Premium VIP",
    "vip_expires_at": "2026-11-06T03:06:32Z",
    "is_active": true,
    "created_at": "2026-10-06T03:00:00Z",
    "updated_at": "2026-10-06T04:06:32Z"
  }
}
```

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test module
pytest tests/test_routes_auth.py -v

# Run with coverage
pytest tests/ --cov=src --cov=production --cov-report=term-missing
```

## Limitations (v1.0.0)

- **Single Account**: Only one active VIP account login at a time
- **No Token Refresh**: Manual re-login required on session expiry
- **Local Persistence**: Session stored in local JSON file (single-instance only)
- **No Streaming**: Video playback and m3u8/DRM handling deferred to v2
- **No Multi-Instance**: Not suitable for distributed deployments

## Roadmap

**v1.1.0:**
- PostgreSQL/Supabase migration for session persistence
- Automated token refresh
- Multi-account support

**v2.0.0:**
- Video streaming endpoints (m3u8, DRM handling)
- History and watchlist
- Recommendations engine

## Architecture

```
FastAPI App (production/main.py)
├── /api/auth/* routes (routes_auth.py)
├── /api/search, /api/feed, /api/drama/* routes (routes_catalog.py)
└── IQIYIClient (src/client/iqiyi_client.py)
    ├── SessionStore (src/client/session_store.py)
    ├── Signer (src/client/signer.py)
    └── PasswordEncryptor (src/utils/crypto.py)
```

**Design Pattern**: Direct Client
- No proxy or playground passthrough routing
- Direct iQIYI API calls authenticated via signed requests
- Session cookie management via local store

## Security Notes

- Credentials encrypted with RSA before transmission to iQIYI
- Session cookies stored locally (not encrypted at rest in v1.0)
- `.env` file with credentials not committed to Git (.gitignore)
- CORS enabled for localhost development

## Production Setup (RSA Key Extraction)

The current implementation uses a placeholder RSA public key. For production:

1. **Extract real RSA key from iQIYI APK**:
   ```bash
   # Decompile APK com.iqiyi.i18n (v8.8.5+)
   apktool d com.iqiyi.i18n.apk
   # Search for RSA public key in classes.dex or decompiled Java files
   # Look in: com.iqiyi.passportsdk or related auth classes
   ```

2. **Update `src/utils/crypto.py`**:
   - Replace `PUBLIC_KEY_PEM` constant with real key extracted from APK
   - Verify key format (PEM encoding)

3. **Test with valid credentials**:
   - Use real iQIYI account (phone/email + password)
   - Login should return 200 with session data

**Current Test Status**:
- RSA encryption: ✅ Working
- Request signing: ✅ Working  
- iQIYI API response: ⏳ Awaiting real RSA key (currently returns `A00006: Signature verification failed`)

## License

Proprietary — Reverse Engineering Project
