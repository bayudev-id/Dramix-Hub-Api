# VIU API Backend

A proxy backend for Viu streaming service, providing custom authentication, caching, paywall bypass for VIP content, and Supabase integration for session management. Built with FastAPI.

## Features

- **Authentication Proxy:** Supports login via Viu, device management, and extracting user profiles.
- **Supabase Integration:** Stores logged-in sessions securely and allows for activating saved sessions.
- **VIP Content Bypass / Fallback:** Automatically tries to fetch playback tokens (m3u8 URLs) and handles VIP paywalls.
- **Streaming Proxy:** Proxies `.m3u8` manifests and DRM keys for secure and customized playback.
- **Auto Guest Token:** Automatically handles guest token generation and retries if a token expires.

## Installation & Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables (e.g., Supabase URL and Key, normally put in a `.env` file or environment).

3. Run the server:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## API Endpoints Documentation

### Authentication (`/api/auth`)

#### `POST /api/auth/login`
Logs a user in using their email or phone number.
- **Payload:** `{"login_id": "email@example.com", "password": "yourpassword"}`
- **Response:** Success status, token, and user info. It automatically saves the session to Supabase and caches the token locally.

#### `POST /api/auth/logout`
Logs out the current active session.
- **Response:** Success message and removes the session from Viu.

#### `GET /api/auth/profile`
Retrieves detailed profile information and list of active devices for the currently logged-in account.
- **Response:** User details, subscription status, and linked devices.

### Supabase Session Management (`/api/supabase`)

#### `GET /api/supabase/sessions`
Retrieves all stored sessions from the Supabase database.
- **Response:** List of stored sessions (emails, created at, etc.).

#### `POST /api/supabase/sessions/activate`
Activates a specific session from Supabase to be used by the backend.
- **Payload:** `{"login_id": "email@example.com"}`
- **Response:** Success message if the session exists and is successfully loaded.

### Playback & Streaming (`/api/playback`, `/vod`, & `/drama-api`)

#### `GET /api/playback/distribute`
Gets the streaming URL (M3U8) for a specific video/product.
- **Query Params:** `product_id` (e.g., `1112345`), `cnd_id` (default: 1)
- **Response:** Contains the direct playback URL or proxied URL for the HLS stream.

#### `GET /vod/vuclip_airplay.m3u8` / `GET /vod/vuclip_vod.m3u8`
Proxied M3U8 routes to manipulate the manifest for bypass and custom keys.

#### `GET /api/drama-api/stream` (Also supports `/drama-api/stream` and `/functions/v1/drama-api/stream`)
Retrieves unified stream URLs and subtitle tracks formatted in a WeTV-compatible structure.
- **Query Params:** 
  - `id`: The series ID (e.g., `103335`).
  - `episode_id`: The episode product ID (e.g., `3095829`).
  - `provider`: Provider identifier (defaults to `"viu"`).
- **Response Format:**
  ```json
  {
      "code": 200,
      "message": "Success",
      "provider": "viu",
      "timestamp": "2026-06-03T18:39:45.014Z [nxh82f]",
      "data": {
          "streams": [
              {
                  "url": "http://127.0.0.1:8000/vod/vuclip_vod.m3u8?...",
                  "quality": "1080p",
                  "format": "hls"
              }
          ],
          "subtitles": [
              {
                  "url": "https://ott-resources.viu.com/...",
                  "lang": "ID",
                  "label": "Bahasa Indonesia"
              }
          ],
          "dubs": []
      }
  }
  ```


#### `GET /api/drama-api/search` (Also supports `/drama-api/search` and `/functions/v1/drama-api/search`)
Search Viu catalog for dramas and movies in a WeTV-compatible structure.
- **Query Params:** 
  - `query` / `keyword` / `q`: The search query string (e.g., `Perfect and Casual`).
  - `page`: Page number (default: `1`).
  - `limit`: Limit of results per page (default: `16`).
  - `provider`: Provider identifier (defaults to `"viu"`).
- **Response Format:**
  ```json
  {
      "code": 200,
      "message": "Success",
      "provider": "viu",
      "data": [
          {
              "id": "103335",
              "title": "Perfect and Casual",
              "cover": "https://prod-images.viu.com/...",
              "cover_portrait": "https://prod-images.viu.com/...",
              "category": "Drama Cina",
              "total_episodes": 24,
              "latest_episode": 24,
              "provider": "viu"
          }
      ]
  }
  ```


### Discovery & Category (`/api/mobile`, `/api/category`, `/api/audienceTargeting`)

#### `GET /api/mobile`
Retrieves mobile catalog/layout data for the homepage.
- **Query Params:** `platform_flag_label` (default: `web`), `area_id` (default: `1000`), `language_flag_id`

#### `GET /api/category`
Retrieves content organized by category.

#### `GET /api/audienceTargeting/recommendations`
Retrieves recommendations for the homepage.

### Config & User Info

#### `GET /api/config`
Retrieves global Viu configuration.

#### `GET /api/user/info`
Retrieves brief user information.

#### `GET /api/subscription/status`
Retrieves the user's current VIP subscription status.

## Error Handling

If `Token is required` is encountered, the backend automatically generates a new guest token using UUIDs and retries the request transparently to the frontend.
