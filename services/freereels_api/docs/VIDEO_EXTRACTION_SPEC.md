# FreeReels Video Extraction Specification

## Overview
Video HLS URLs tersedia langsung dari endpoint `/drama/info_v2` tanpa memerlukan endpoint terpisah untuk download/play.

## Endpoint
```
GET /frv2-api/drama/info_v2
```

### Query Parameters
| Parameter | Required | Description |
|-----------|----------|-------------|
| `series_id` | ✅ | Drama ID (e.g., `eAiS7aYiYQ`) |
| `scene` | ✅ | Scene identifier (usually `"1"`) |

### Response Structure
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "info": { ... },
    "list": [ ... ]  // episode list (may be empty, check info.episode_list)
  }
}
```

## Video URLs Location
Video URLs berada di `data.info.episode_list[]`, bukan di `data.list`.

### Episode Object Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Episode ID |
| `index` | int | Episode number (1-based) |
| `external_audio_h264_m3u8` | string | **HLS master playlist (H.264)** |
| `external_audio_h265_m3u8` | string | **HLS master playlist (H.265)** |
| `subtitle_list[]` | array | Multi-language subtitles (SRT + VTT) |
| `duration` | int | Video duration in seconds |
| `unlock` | bool | Episode unlocked for current user |
| `video_type` | string | `"free"` or `"paid"` |
| `episode_price` | int | Coin price if locked |
| `trans_resolution` | string | Available resolutions: `"720x1280,540x960,480x854,360x640,240x426"` |
| `sprite_vtt_url` | string | Thumbnail sprite VTT for seeking |
| `sprite_urls[]` | array | Thumbnail sprite images |

## HLS Video Format

### Master Playlist
URLs point to HLS master playlists (`.m3u8`) yang berisi multiple bitrate variants.

```
https://video-v6.mydramawave.com/vt/{uuid}/h264-{uuid}.m3u8
https://video-v6.mydramawave.com/vt/{uuid}/h265-{uuid}.m3u8
```

Domain CDN video: `video-v6.mydramawave.com`, `video-v81.mydramawave.com`

### Resolution Variants
Berdasarkan field `trans_resolution`, tersedia 5 varian:
- 720x1280 (720p portrait)
- 540x960 (540p)
- 480x854 (480p)
- 360x640 (360p)
- 240x426 (240p)

### Access Control
Video URLs **tidak memerlukan authentication token** — dapat diakses langsung via HTTP GET tanpa Authorization header.

Server hanya memeriksa access control di level API endpoint (`/drama/info_v2`), bukan di level CDN video.

## Subtitle Format

### Subtitle Object
```json
{
  "language": "id-ID",
  "type": "original",
  "subtitle": "https://video-v81.mydramawave.com/vt/22100/fc0aba4c-ee4d-4cd6-bf5d-77fe27abd0e2.srt",
  "vtt": "https://video-v6.mydramawave.com/ut/22100/1_4e096564-4ea3-4985-8d18-36b15bd508e5.vtt",
  "display_name": "Indonesia"
}
```

| Field | Description |
|-------|-------------|
| `language` | ISO language code (e.g., `id-ID`, `en-US`, `ja-JP`) |
| `type` | `"original"` atau `"normal"` (translated) |
| `subtitle` | SRT format subtitle URL |
| `vtt` | WebVTT format subtitle URL |
| `display_name` | Localized language name |

Domain CDN subtitle: `video-v6.mydramawave.com`, `video-v81.mydramawave.com`

## Python Example

```python
from freereels_client import FreeReelsClient
import json

client = FreeReelsClient()
client.login_anonymous()

# Fetch drama info
drama = client._request(
    "GET",
    "/frv2-api/drama/info_v2",
    params={"series_id": "eAiS7aYiYQ", "scene": "1"}
)

info = drama["info"]
episodes = info["episode_list"]

for ep in episodes:
    print(f"Episode {ep['index']}: {ep.get('duration')}s")
    print(f"  H.264: {ep['external_audio_h264_m3u8']}")
    print(f"  H.265: {ep['external_audio_h265_m3u8']}")
    print(f"  Unlocked: {ep['unlock']}")
    print(f"  Subtitles: {len(ep['subtitle_list'])} languages")
```

## Download Strategy

1. **Fetch episode list** via `/drama/info_v2`
2. **Check `unlock` field** — if `false`, episode requires payment
3. **Download HLS master playlist** from `external_audio_h264_m3u8` or `external_audio_h265_m3u8`
4. **Parse master playlist** to get variant playlists (by resolution)
5. **Download selected variant playlist**
6. **Download all TS segments** referenced in variant playlist
7. **Concatenate segments** to single video file
8. **Download subtitles** from `subtitle_list[]` (optional)

### Recommended Tools
- `ffmpeg` with HLS support: `ffmpeg -i <m3u8_url> -c copy output.mp4`
- `yt-dlp`: `yt-dlp <m3u8_url>`
- `streamlink`: `streamlink <m3u8_url> best -o output.mp4`

## Locked Episodes (VIP/Paid)

Episodes dengan `unlock: false` memerlukan:
1. **Payment** via `/pay/pay_series` atau `/pay/pay_episode`
2. **VIP subscription** (endpoint: `/vip/...`)
3. **Ad watching** (endpoint: `/advertise/...`)

Mekanisme unlock **server-side** — client tidak bisa bypass dengan modify request.

## Notes

1. Video URLs valid untuk waktu tertentu (expiry tidak terlihat di response, kemungkinan 24-48 jam)
2. CDN domain kadang berbeda (`video-v6`, `video-v81`, dll) — semua valid
3. Tidak ada DRM/encryption pada video segments — plain HLS
4. Tidak ada rate limiting terdeteksi di level CDN (per 2026-10-04)
