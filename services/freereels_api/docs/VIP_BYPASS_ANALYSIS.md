# FreeReels VIP/Lock Bypass Analysis

## Executive Summary
FreeReels implements **client-side-only** episode locking. Video URLs are embedded in API responses regardless of lock status, and CDN servers do not enforce authentication.

## Lock Mechanism Analysis

### API Layer (Server-Side)
- Endpoint `/drama/download` returns `403 Permission denied` for locked episodes
- Episode object in `/drama/info_v2` contains field `"locked": true` for paid content
- Field `"video_type"` paradoxically shows `"free"` even when `locked: true`

### CDN Layer (Video Delivery)
- Video URLs are **always present** in `external_audio_h264_m3u8` and `external_audio_h265_m3u8` fields
- CDN servers (`video-v6.mydramawave.com`, `video-v81.mydramawave.com`) do **NOT** require authentication
- Direct HLS playlist requests return `200 OK` without any auth headers
- Master playlists include adaptive bitrate variants (240p to 720p)

## Bypass Method

### Without Exploit
Standard API flow requires unlock via `/drama/unlock_episode` (payment endpoint).

### With Bypass
1. Call `/drama/info_v2?series_id={id}&scene=1` with guest OAuth token
2. Extract `episode.external_audio_h264_m3u8` from response
3. Access URL directly via HTTP GET (no auth headers needed)
4. Parse HLS master playlist and download video segments

### Code Example
```python
from freereels_client import FreeReelsClient

client = FreeReelsClient()
client.login_anonymous()

# Get drama info
drama = client._request("GET", "/frv2-api/drama/info_v2", params={
    "series_id": "eAiS7aYiYQ",
    "scene": "1"
})

# Extract video URLs from locked episodes
for episode in drama["info"]["episode_list"]:
    video_url = episode["external_audio_h264_m3u8"]
    print(f"Episode {episode['id']}: {video_url}")
    # Video URL is accessible without further authentication
```

## Evidence

### Test Case: "Monster? Aku Terikat dengan Dewi" (series_id: eAiS7aYiYQ)
- Total episodes: 58
- Lock status: All 58 marked as `"locked": true`
- Video URL availability: **58/58 (100%)**
- CDN access test: **SUCCESS** (200 OK, no auth required)

### Sample Direct Access
```
URL: https://video-v6.mydramawave.com/vt/d81b16e0-e664-49dc-82af-b96c03fdb50e/h264-3179fcf0-10ea-45b0-a1a0-0455b07e9791.m3u8
Method: GET
Headers: User-Agent, Referer (optional)
Response: 200 OK
Content-Type: audio/x-mpegurl
```

Master playlist contains:
- 5 video quality variants (240p, 360p, 480p, 540p, 720p)
- Separate audio track
- Adaptive bitrate streaming support

## Root Cause
Design flaw: API endpoint `/drama/download` enforces authorization, but the data structure returned by `/drama/info_v2` **already contains the final video URLs** before authorization check. CDN assumes URLs are pre-authorized by API layer.

## Impact
All premium/locked content accessible without payment. VIP subscription and per-episode unlock mechanisms completely bypassed.

## Recommendations (If Working for FreeReels Security Team)
1. Remove `external_audio_*_m3u8` fields from `/drama/info_v2` response for locked episodes
2. Implement signed URL tokens on CDN with short expiration (AWS CloudFront signed URLs pattern)
3. Move video URL generation to `/drama/download` endpoint after successful authorization
4. Add referrer validation and rate limiting on CDN
5. Implement DRM (Widevine/FairPlay) for premium content

## Technical Details
- API Base: `https://apiv2.free-reels.com/frv2-api/`
- CDN Domains: `video-v6.mydramawave.com`, `video-v81.mydramawave.com`
- Video Format: HLS (HTTP Live Streaming) with H.264/H.265 codecs
- Auth Required: API endpoints (OAuth signature)
- Auth NOT Required: CDN video delivery

## Output Files
- `output/monster_videos.json`: Full extraction of 58 locked episodes with accessible URLs
- `src/extract_videos.py`: Automated extraction script for any drama series
