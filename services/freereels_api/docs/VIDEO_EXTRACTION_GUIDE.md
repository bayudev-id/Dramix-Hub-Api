# FreeReels Video Extraction - Complete Guide

## Overview
HLS video URLs tersedia langsung dari `/drama/info_v2` endpoint tanpa perlu endpoint `/drama/download` terpisah.

## Video URL Structure

### Endpoint
```
GET /frv2-api/drama/info_v2
```

**Parameters:**
- `series_id`: Drama ID (e.g., `eAiS7aYiYQ`)
- `scene`: Context identifier (e.g., `"1"`)

**Auth:** Requires OAuth signature header

### Response Structure
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "info": {
      "id": "eAiS7aYiYQ",
      "name": "Monster? Aku Terikat dengan Dewi",
      "episode_count": 58,
      "episode_list": [
        {
          "id": "3e7Ltchsvg",
          "index": 1,
          "name": "Monster? Aku Terikat dengan Dewi",
          "video_type": "free",
          "unlock": true,
          "episode_price": 60,
          "external_audio_h264_m3u8": "https://video-v6.mydramawave.com/vt/.../h264-....m3u8",
          "external_audio_h265_m3u8": "https://video-v6.mydramawave.com/vt/.../h265-....m3u8",
          "duration": 158,
          "subtitle_list": [...]
        }
      ]
    }
  }
}
```

### Key Fields

| Field | Type | Description |
|-------|------|-------------|
| `external_audio_h264_m3u8` | string | HLS master playlist URL (H.264 codec) |
| `external_audio_h265_m3u8` | string | HLS master playlist URL (H.265 codec) |
| `video_type` | string | `"free"` or `"vip"` or `"paid"` |
| `unlock` | boolean | Whether episode is unlocked for current user |
| `episode_price` | integer | Coin price if locked |
| `subtitle_list` | array | Available subtitles in 25+ languages |

## Video Access

### Free Episodes
Free episodes (`video_type: "free"`) are accessible directly:

```python
import requests

m3u8_url = episode["external_audio_h264_m3u8"]
response = requests.get(m3u8_url, timeout=10)

if response.status_code == 200:
    # M3U8 playlist fetched successfully
    print(response.text)
```

**No additional authentication required** for accessing HLS URLs.

### VIP/Paid Episodes
Locked episodes have:
- `unlock: false`
- `episode_price: <coin_amount>`
- `video_type: "vip"` or `"paid"`

**Access mechanism:**
1. Server returns empty string for HLS URLs if episode locked at API level, OR
2. Server returns HLS URL but CDN returns 403 Forbidden

*Note: As of test date (Oct 2026), all dramas in Indonesian homepage are fully free.*

## HLS Playlist Structure

### Master Playlist
```m3u8
#EXTM3U
#EXT-X-INDEPENDENT-SEGMENTS
#EXT-X-MEDIA:TYPE=AUDIO,URI="...aac.m3u8",GROUP-ID="default-audio-group"
#EXT-X-STREAM-INF:BANDWIDTH=2073718,RESOLUTION=720x1280,FRAME-RATE=25.000
1_..._1301549_0.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=1309977,RESOLUTION=540x960,FRAME-RATE=25.000
1_..._1301549_1.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=853897,RESOLUTION=360x640,FRAME-RATE=25.000
1_..._1301549_3.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=497873,RESOLUTION=240x426,FRAME-RATE=25.000
1_..._1301549_4.m3u8
```

### Available Resolutions
- **720x1280** (720p) - 2.07 Mbps
- **540x960** (540p) - 1.31 Mbps
- **480x854** (480p) - 1.18 Mbps
- **360x640** (360p) - 0.85 Mbps
- **240x426** (240p) - 0.50 Mbps

All variants use H.264 (AVC) codec with AAC audio.

## Subtitle Extraction

### Structure
Each episode includes `subtitle_list` with 25+ languages:

```json
{
  "language": "en-US",
  "type": "normal",
  "subtitle": "https://video-v6.mydramawave.com/vt/22100/....srt",
  "vtt": "https://video-v6.mydramawave.com/ut/22100/....vtt",
  "display_name": "Inggris"
}
```

### Available Languages
Indonesian (original), English, Spanish, Portuguese, French, German, Italian, Russian, Arabic, Hindi, Tamil, Telugu, Bengali, Thai, Vietnamese, Filipino, Malay, Japanese, Korean, Traditional Chinese, Polish, Czech, Romanian, Greek, Turkish

### Format
- **SRT**: Standard SubRip format
- **VTT**: WebVTT format (web-compatible)

Both formats are directly accessible via HTTPS (no auth required).

## Python Implementation

```python
from freereels_client import FreeReelsClient

# Initialize and login
client = FreeReelsClient()
client.login_anonymous()

# Get drama info with episodes
drama = client._request("GET", "/frv2-api/drama/info_v2", params={
    "series_id": "eAiS7aYiYQ",
    "scene": "1"
})

episodes = drama["info"]["episode_list"]

for episode in episodes:
    if episode["video_type"] == "free":
        print(f"Episode {episode['index']}: {episode['name']}")
        print(f"  H.264: {episode['external_audio_h264_m3u8']}")
        print(f"  Duration: {episode['duration']}s")
        
        # Download subtitles
        for sub in episode["subtitle_list"]:
            if sub["language"] == "en-US":
                print(f"  English subtitle: {sub['vtt']}")
```

## Download Strategy

### Option 1: Direct HLS Download
Use `ffmpeg` to download and merge HLS segments:

```bash
ffmpeg -i "https://video-v6.mydramawave.com/vt/.../h264-....m3u8" \
       -c copy \
       -bsf:a aac_adtstoasc \
       output.mp4
```

### Option 2: Segment Download
Parse M3U8 playlist and download `.ts` segments individually, then concatenate.

### Option 3: Python Streaming
Use `streamlink` or `m3u8` library to download:

```python
import m3u8
import requests

playlist_url = episode["external_audio_h264_m3u8"]
playlist = m3u8.load(playlist_url)

# Get highest quality variant
best_variant = max(playlist.playlists, key=lambda p: p.stream_info.bandwidth)
variant_url = best_variant.absolute_uri

# Download variant playlist and segments
variant_playlist = m3u8.load(variant_url)
for segment in variant_playlist.segments:
    segment_url = segment.absolute_uri
    # Download segment_url
```

## Response Encryption

**Note:** `/drama/info_v2` responses may be encrypted (indicated by `x-decry: 1` header).

Decryption is handled automatically by `FreeReelsClient` using AES-128-CBC with extracted native keys.

See `docs/RESPONSE_DECRYPTION_SPEC.md` for details.

## Verification

**Test results (2026-10-04):**
- ✅ HLS URLs accessible for free episodes (HTTP 200)
- ✅ Adaptive bitrate streaming working (240p-720p)
- ✅ Subtitles in 25 languages accessible
- ✅ M3U8 playlists parseable and segments downloadable
- ✅ No additional auth required beyond initial OAuth token

## VIP Unlock Mechanism

**Status:** Not yet analyzed (no VIP-locked dramas found in test sample).

**Expected behavior based on API structure:**
1. Client sends payment request with episode_id and coin amount
2. Server updates user balance and sets `unlock: true` for episode
3. Subsequent `/drama/info_v2` requests return HLS URLs for unlocked episodes

**Potential bypass:** Check if HLS URLs are predictable or if CDN validates unlock status separately from API.

*Further analysis required when VIP-locked content is available.*
