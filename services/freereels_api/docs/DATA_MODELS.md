# FreeReels API - Data Models Documentation

Complete data model specifications extracted from live API responses.

**Last Updated:** 2026-10-04  
**API Version:** FreeReels 2.4.91  
**Source:** Reverse engineering via Frida + JADX + live traffic analysis

---

## Table of Contents

1. [Authentication Models](#authentication-models)
2. [Homepage & Feed Models](#homepage--feed-models)
3. [Drama Models](#drama-models)
4. [Episode Models](#episode-models)
5. [User Models](#user-models)
6. [Search Models](#search-models)
7. [Pagination Models](#pagination-models)

---

## Authentication Models

### AnonymousLoginRequest
```json
{
  "device_id": "da9ce769379941e4",
  "device_name": "Xiaomi Redmi 5 Plus",
  "sign": "3f043f1baa7791ce8a242197e8c6d4a1"
}
```

**Fields:**
- `device_id` (string, required): 16-char hex device identifier
- `device_name` (string, required): Device model name
- `sign` (string, required): MD5 signature = `MD5("8IAcbWyCsVhYv82S2eofRqK1DF3nNDAv" + device_id)`

### AnonymousLoginResponse
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "user_id": 75954315519,
    "name": "Tamu",
    "auth_key": "a72W5LyH2yFSqkr",
    "auth_secret": "xK9mPq3LsWd",
    "avatar": "https://static-v1.mydramawave.com/default_avatar.png",
    "country": "ID",
    "language": "id-ID"
  }
}
```

**Fields:**
- `code` (integer): 0 or 200 = success, others = error
- `message` (string): Human-readable status
- `data.user_id` (integer): Unique user ID
- `data.auth_key` (string): OAuth token for subsequent requests
- `data.auth_secret` (string): Secret for OAuth signature generation

### OAuth Signature Format
HTTP Header:
```
Authorization: oauth_signature={MD5_HEX},oauth_token={auth_key},ts={timestamp_ms}
```

Signature calculation:
```
oauth_signature = MD5("8IAcbWyCsVhYv82S2eofRqK1DF3nNDAv&" + endpoint + "?" + sorted_query_params + timestamp_ms + auth_secret)
```

---

## Homepage & Feed Models

### TabListResponse
**Endpoint:** `GET /frv2-api/homepage/v2/tab/list`

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "list": [
      {
        "name": "Populer",
        "tab_key": "503",
        "business_name": "popular",
        "type": 1,
        "icon": "https://static-v1.mydramawave.com/icons/popular.png"
      }
    ]
  }
}
```

**Tab Types (CategoryTabType enum):**
- `1` = DRAMA
- `2` = NOVEL
- `3` = MIX
- `4` = COMICS
- `10` = HOT_LIST
- `100` = CATEGORY_FILTER
- `1000` = H5_ACTIVITY

**Known Tabs:**
| tab_key | name | business_name | type |
|---------|------|---------------|------|
| 503 | Populer | popular | 1 |
| 504 | Perempuan | female | 1 |
| 505 | New | new | 1 |
| 506 | Laki-Laki | male | 1 |
| 516 | Dubbing | doblaje | 1 |
| 547 | Anime | anime | 1 (hidden from tab/list) |
| 622 | Segera hadir | comingsoon | 1 |

---

### HomepageTabIndexResponse
**Endpoint:** `GET /frv2-api/homepage/v2/tab/index`

Query params:
- `tab_key`: Category key (503, 505, 516, etc.)
- `position_index`: Pagination cursor (default: 10000)
- `rec_trigger`: Recommendation trigger (default: 1)

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "module_key": "1065",
        "module_name": "Rekomendasi",
        "items": [
          {
            "key": "QCJvQG2LLD",
            "title": "Master Judi Jadi Suami Rumah Tangga(Sulih Suara)",
            "cover": "https://static-v1.mydramawave.com/vt/prod/cover/uuid.jpg",
            "desc": "Drama description...",
            "episode_count": 61,
            "follow_count": 109991,
            "view_count": 0,
            "tag": ["Gratis"],
            "series_tag": [""],
            "content_tags": ["Balas Dendam", "Miskin Jadi Kaya"],
            "operation_tags": [
              {
                "text": "Dubbing",
                "text_color": "#FFFFFF",
                "bg_start": "#F47040",
                "bg_end": "#F52067",
                "tag_type": ""
              }
            ],
            "free": 5,
            "pay_index": 6,
            "finish_status": 1,
            "update_count": 0,
            "vip_type": 2,
            "orientation": "vertical",
            "link": "freereels://series_detail?key=QCJvQG2LLD",
            "link_type": 0,
            "resource_type": 1,
            "episode_info": {
              "id": "LJ5YLRyTpX",
              "name": "Master Judi Jadi Suami Rumah Tangga(Sulih Suara)",
              "cover": "https://static-v1.mydramawave.com/episode_cover.jpg",
              "video_url": "",
              "m3u8_url": "",
              "external_audio_h264_m3u8": "https://video-v6.mydramawave.com/vt/uuid/h264.m3u8",
              "external_audio_h265_m3u8": "https://video-v81.mydramawave.com/vt/uuid/h265.m3u8",
              "subtitle_list": [
                {
                  "language": "id-ID",
                  "type": "normal",
                  "subtitle": "https://video-v81.mydramawave.com/ut/uuid.srt",
                  "vtt": "https://video-v6.mydramawave.com/ut/uuid.vtt",
                  "display_name": "Indonesian"
                }
              ]
            }
          }
        ]
      }
    ],
    "page_info": {
      "next": "last_quality=0&offset=10&position_index=10000&timestamp=",
      "has_more": true
    }
  }
}
```

---

### HomepageTabFeedResponse
**Endpoint:** `POST /frv2-api/homepage/v2/tab/feed`

Request body:
```json
{
  "next": "last_quality=0&offset=0&position_index=10000&timestamp=",
  "user_new_theater": false,
  "module_key": "1065"
}
```

Response:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "key": "QCJvQG2LLD",
        "title": "...",
        "cover": "...",
        "desc": "...",
        "episode_count": 61,
        "follow_count": 109991,
        "view_count": 0,
        "tag": ["Gratis"],
        "content_tags": ["Balas Dendam"],
        "operation_tags": [...],
        "free": 5,
        "pay_index": 6,
        "vip_type": 2,
        "episode_info": {...}
      }
    ],
    "page_info": {
      "next": "last_quality=0&offset=10&position_index=10000&timestamp=",
      "has_more": true
    },
    "module_name": "Rekomendasi"
  }
}
```

**Note:** This endpoint provides better pagination than `/homepage/v2/tab/index` and is used by the app during scroll.

---

## Drama Models

### DramaItem (Homepage/Feed Item)

**Core Fields:**
- `key` (string): Unique drama identifier (e.g., "QCJvQG2LLD")
- `title` (string): Drama title (localized)
- `cover` (string): Cover image URL (WebP format, CDN)
- `desc` (string): Drama description/synopsis

**Metadata:**
- `episode_count` (integer): Total number of episodes
- `follow_count` (integer): Number of users following this drama
- `view_count` (integer): Total view count (often 0)
- `finish_status` (integer): 0=ongoing, 1=completed
- `update_count` (integer): Number of new episodes since last view
- `orientation` (string): "vertical" or "horizontal"

**Monetization:**
- `free` (integer): Number of free episodes
- `pay_index` (integer): First paid episode number
- `vip_type` (integer): 0=free, 1=coins, 2=VIP subscription
- `tag` (array[string]): Display tags like ["Gratis", "VIP", "Baru"]

**Categories & Tags:**
- `content_tags` (array[string]): Genre/theme tags (e.g., "Balas Dendam", "Miskin Jadi Kaya")
- `series_tag` (array[string]): Series tags (often empty)
- `content_detail_tags` (array[string]|null): Detailed tags
- `operation_tags` (array[OperationTag]): Special visual tags with colors

**Navigation:**
- `link` (string): Deep link URI (e.g., "freereels://series_detail?key=QCJvQG2LLD")
- `link_type` (integer): 0=drama detail, other values TBD
- `resource_type` (integer): 1=drama, other values TBD

**Episode Preview:**
- `episode_info` (EpisodeInfo): First episode metadata (see Episode Models)

**Advanced Fields:**
- `hot_score` (float): Popularity score for ranking
- `r_info` (string): Recommendation info
- `r_info1` (string): Additional recommendation data
- `module_card` (object): UI card layout info
- `style` (string): Visual style identifier

---

### OperationTag
```json
{
  "text": "Dubbing",
  "text_color": "#FFFFFF",
  "bg_start": "#F47040",
  "bg_end": "#F52067",
  "tag_type": ""
}
```

**Fields:**
- `text` (string): Tag label
- `text_color` (string): Text color hex
- `bg_start` (string): Gradient start color
- `bg_end` (string): Gradient end color
- `tag_type` (string): Tag category (often empty)

---

### DramaDetailResponse
**Endpoint:** `GET /frv2-api/drama/info_v2`

Query params:
- `series_id`: Drama key (e.g., "QCJvQG2LLD")
- `scene`: Entry point (e.g., "homepage", "search")
- `clip_content`: 0 or 1
- `campaign`: Campaign ID (optional)

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "series_id": "QCJvQG2LLD",
    "name": "Master Judi Jadi Suami Rumah Tangga(Sulih Suara)",
    "cover": "https://static-v1.mydramawave.com/cover.jpg",
    "horizontal_cover": "https://static-v1.mydramawave.com/h_cover.jpg",
    "desc": "Full description...",
    "director": "Zhang Wei",
    "actor": "Liu Yang, Chen Xiao",
    "release_year": 2024,
    "total_episodes": 61,
    "follow_count": 109991,
    "view_count": 1234567,
    "like_count": 8900,
    "is_followed": false,
    "is_liked": false,
    "content_tags": ["Romance", "Drama"],
    "episodes": [
      {
        "id": "LJ5YLRyTpX",
        "index": 1,
        "name": "Episode 1",
        "cover": "https://static-v1.mydramawave.com/ep_cover.jpg",
        "duration": 180,
        "is_free": true,
        "is_unlocked": false,
        "unlock_price": 0,
        "video_url": "",
        "m3u8_url": "",
        "external_audio_h264_m3u8": "https://video-v6.mydramawave.com/h264.m3u8",
        "external_audio_h265_m3u8": "https://video-v81.mydramawave.com/h265.m3u8",
        "subtitle_list": [...]
      }
    ],
    "related_series": [
      {
        "key": "ABC123",
        "title": "Similar Drama",
        "cover": "https://...",
        "episode_count": 50
      }
    ]
  }
}
```

**Fields:**
- `series_id` (string): Drama unique ID
- `name` (string): Full title
- `cover` (string): Vertical cover image
- `horizontal_cover` (string): Horizontal cover (for landscape)
- `desc` (string): Full synopsis
- `director` (string): Director name
- `actor` (string): Comma-separated actor names
- `release_year` (integer): Release year
- `total_episodes` (integer): Total episode count
- `follow_count`, `view_count`, `like_count` (integer): Engagement metrics
- `is_followed`, `is_liked` (boolean): User interaction state
- `content_tags` (array[string]): Genre tags
- `episodes` (array[Episode]): Full episode list with video URLs
- `related_series` (array[DramaItem]): Recommended similar dramas

---

## Episode Models

### EpisodeInfo (Preview in Feed)
```json
{
  "id": "LJ5YLRyTpX",
  "name": "Episode 1 Title",
  "cover": "https://static-v1.mydramawave.com/episode_cover.jpg",
  "video_url": "",
  "m3u8_url": "",
  "external_audio_h264_m3u8": "https://video-v6.mydramawave.com/vt/uuid/h264.m3u8",
  "external_audio_h265_m3u8": "https://video-v81.mydramawave.com/vt/uuid/h265.m3u8",
  "subtitle_list": [
    {
      "language": "id-ID",
      "type": "normal",
      "subtitle": "https://video-v81.mydramawave.com/ut/uuid.srt",
      "vtt": "https://video-v6.mydramawave.com/ut/uuid.vtt",
      "display_name": "Indonesian"
    }
  ]
}
```

**Fields:**
- `id` (string): Episode unique ID
- `name` (string): Episode title/name
- `cover` (string): Episode thumbnail
- `video_url` (string): Legacy field (usually empty)
- `m3u8_url` (string): Legacy field (usually empty)
- `external_audio_h264_m3u8` (string): HLS master playlist H.264 (primary)
- `external_audio_h265_m3u8` (string): HLS master playlist H.265 (HEVC)
- `subtitle_list` (array[Subtitle]): Available subtitle tracks

---

### Episode (Full Detail)
```json
{
  "id": "LJ5YLRyTpX",
  "index": 1,
  "name": "Episode 1",
  "cover": "https://static-v1.mydramawave.com/ep_cover.jpg",
  "duration": 180,
  "is_free": true,
  "is_unlocked": false,
  "unlock_price": 0,
  "unlock_type": 1,
  "video_url": "",
  "m3u8_url": "",
  "external_audio_h264_m3u8": "https://video-v6.mydramawave.com/h264.m3u8",
  "external_audio_h265_m3u8": "https://video-v81.mydramawave.com/h265.m3u8",
  "subtitle_list": [...]
}
```

**Additional Fields:**
- `index` (integer): Episode number (1-based)
- `duration` (integer): Duration in seconds
- `is_free` (boolean): Free to watch without unlock
- `is_unlocked` (boolean): User has unlocked this episode
- `unlock_price` (integer): Price in coins to unlock
- `unlock_type` (integer): 0=free, 1=coins, 2=VIP

---

### Subtitle
```json
{
  "language": "id-ID",
  "type": "normal",
  "subtitle": "https://video-v81.mydramawave.com/ut/19029/1_uuid.srt",
  "vtt": "https://video-v6.mydramawave.com/ut/19029/1_uuid.vtt",
  "display_name": "Indonesian"
}
```

**Fields:**
- `language` (string): Language code (ISO 639-1 + ISO 3166-1, e.g., "id-ID")
- `type` (string): "normal" or "ai" (AI-generated)
- `subtitle` (string): SRT subtitle file URL
- `vtt` (string): WebVTT subtitle file URL
- `display_name` (string): Human-readable language name

**Supported Languages (25 total):**
- Indonesian (id-ID)
- English (en-US)
- Spanish (es-ES)
- Portuguese (pt-BR)
- French (fr-FR)
- German (de-DE)
- Italian (it-IT)
- Russian (ru-RU)
- Arabic (ar-SA)
- Hindi (hi-IN)
- Tamil (ta-IN)
- Telugu (te-IN)
- Bengali (bn-BD)
- Thai (th-TH)
- Vietnamese (vi-VN)
- Filipino (fil-PH)
- Malay (ms-MY)
- Japanese (ja-JP)
- Korean (ko-KR)
- Chinese Traditional (zh-TW)
- Polish (pl-PL)
- Turkish (tr-TR)
- Urdu (ur-PK)
- Marathi (mr-IN)
- Kannada (kn-IN)

---

### HLS Video Quality Tiers
Master playlist (`external_audio_h264_m3u8`) contains variants:

| Resolution | Bitrate | Format |
|------------|---------|--------|
| 240p | ~400 Kbps | H.264 |
| 360p | ~800 Kbps | H.264 |
| 480p | ~1200 Kbps | H.264 |
| 540p | ~1500 Kbps | H.264 |
| 720p | ~2500 Kbps | H.264 |

HEVC variants (`external_audio_h265_m3u8`) available for same resolutions at ~30% lower bitrate.

---

## User Models

### UserProfile
**Endpoint:** `GET /frv2-api/user/profilev2`

```json
{
  "code": 0,
  "data": {
    "user_id": 75954315519,
    "name": "Tamu",
    "avatar": "https://static-v1.mydramawave.com/avatar.png",
    "email": "",
    "phone": "",
    "country": "ID",
    "language": "id-ID",
    "vip_info": {
      "is_vip": false,
      "vip_type": 0,
      "expire_time": 0
    },
    "wallet": {
      "coins": 0,
      "free_coins": 0
    },
    "stats": {
      "follow_count": 0,
      "history_count": 0,
      "like_count": 0
    }
  }
}
```

---

## Search Models

### SearchRequest
**Endpoint:** `POST /frv2-api/search/drama`

```json
{
  "keyword": "love",
  "type": "drama",
  "page": 1,
  "page_size": 20
}
```

### SearchResponse
```json
{
  "code": 0,
  "data": {
    "list": [
      {
        "key": "ABC123",
        "title": "Love Story",
        "cover": "https://...",
        "episode_count": 30,
        "content_tags": ["Romance"]
      }
    ],
    "total": 156,
    "page": 1,
    "page_size": 20
  }
}
```

---

## Pagination Models

### PageInfo (Standard)
```json
{
  "next": "last_quality=0&offset=10&position_index=10000&timestamp=",
  "has_more": true
}
```

**Fields:**
- `next` (string): Opaque pagination token (query string format)
- `has_more` (boolean): True if more pages exist

**Usage:**
- For `GET /homepage/v2/tab/index`: Parse `next` string, extract parameters, pass via query params
- For `POST /homepage/v2/tab/feed`: Send entire `next` string in request body

**Pagination Parameters (Internal):**
- `last_quality` (integer): Quality filter (0=all)
- `offset` (integer): Item offset (increments by 10 per page)
- `position_index` (integer): Recommendation cursor (default: 10000)
- `timestamp` (string): Server timestamp (usually empty)

**Note:** Server may return same `next` value across multiple pages, indicating end of content. Detect duplicates via drama `key` field.

---

## Response Encryption

Some responses are AES-128-CBC encrypted (indicated by `x-decry: 1` header).

**Format:**
```
Base64(IV_16_bytes || AES_CBC_Ciphertext || PKCS7_Padding)
```

**Keys (from libdwguard.so):**
- Flavor 1: `3sa9Kx7mQu3Ls8Wd`
- Flavor 2: `79psatnvfgktswba`

**Decryption Steps:**
1. Base64 decode response body
2. Extract IV (first 16 bytes)
3. Extract ciphertext (remaining bytes)
4. Try each key with AES-128-CBC
5. Remove PKCS7 padding
6. UTF-8 decode plaintext JSON

**Auto-Decryption:** Implemented in `FreeReelsClient._request()` method.

---

## Error Response Format

All endpoints use consistent error format:

```json
{
  "code": 600,
  "message": "Resource not found",
  "data": null
}
```

**Common Error Codes:**
- `0` or `200`: Success
- `401`: Unauthorized (invalid/expired OAuth token)
- `403`: Forbidden (VIP content, region lock)
- `404`: Not found
- `600`: Generic error (empty category, invalid parameter)

---

## Constants & Enums

### VIP Types
```python
VIP_TYPE_FREE = 0        # Free content
VIP_TYPE_COINS = 1       # Unlock with coins
VIP_TYPE_SUBSCRIPTION = 2  # Requires VIP subscription
```

### Finish Status
```python
FINISH_STATUS_ONGOING = 0
FINISH_STATUS_COMPLETED = 1
```

### Link Types
```python
LINK_TYPE_DRAMA_DETAIL = 0
LINK_TYPE_EXTERNAL = 1
LINK_TYPE_H5_PAGE = 2
```

### Resource Types
```python
RESOURCE_TYPE_DRAMA = 1
RESOURCE_TYPE_NOVEL = 2
RESOURCE_TYPE_COMIC = 3
```

---

## CDN & Media Infrastructure

**Static Assets CDN:**
- `https://static-v1.mydramawave.com/` - Covers, avatars, icons

**Video CDN (Multi-Region):**
- `https://video-v6.mydramawave.com/` - Primary video CDN
- `https://video-v81.mydramawave.com/` - Secondary video CDN

**Image Processing:**
```
?image_process=quality,85/resize,w_600/format,webp
```

**URL Parameters:**
- `quality`: JPEG/WebP quality (0-100)
- `resize`: Width/height constraint
- `format`: Output format (webp, jpeg, png)

---

## Usage Examples

### Python Client - Fetch Homepage Feed

```python
from freereels_client import FreeReelsClient

client = FreeReelsClient()
client.login_anonymous()

# Get all tabs
tabs = client.get_homepage_tabs()
for tab in tabs:
    print(f"{tab['name']} (tab_key: {tab['tab_key']})")

# Get dramas from Popular category
dramas = client.get_dramas_by_category(tab_key="503")
for drama in dramas:
    print(f"{drama['title']} - {drama['episode_count']} episodes")
```

### Python Client - Get Drama Detail

```python
# Get full drama info with episodes
drama_detail = client._request("GET", "/frv2-api/drama/info_v2", params={
    "series_id": "QCJvQG2LLD",
    "scene": "homepage"
})

episodes = drama_detail["data"]["episodes"]
for ep in episodes:
    if ep["is_free"]:
        print(f"Episode {ep['index']}: {ep['external_audio_h264_m3u8']}")
```

### Pagination Example

```python
offset = 0
all_dramas = []

while True:
    payload = {
        "next": f"last_quality=0&offset={offset}&position_index=10000&timestamp=",
        "user_new_theater": False,
        "module_key": "1065"
    }
    
    resp = client._request("POST", "/frv2-api/homepage/v2/tab/feed", json=payload)
    
    if not resp or not resp.get("items"):
        break
    
    items = resp["items"]
    page_info = resp.get("page_info", {})
    
    # Check for duplicates
    new_count = 0
    for item in items:
        drama_id = item["key"]
        if drama_id not in seen_ids:
            seen_ids.add(drama_id)
            all_dramas.append(item)
            new_count += 1
    
    if new_count == 0 or not page_info.get("has_more"):
        break
    
    offset += 10
```

---

## Changelog

**v1.0.0 (2026-10-04)**
- Initial documentation
- All models extracted from live API responses
- Verified with FreeReels 2.4.91

---

**End of Documentation**
