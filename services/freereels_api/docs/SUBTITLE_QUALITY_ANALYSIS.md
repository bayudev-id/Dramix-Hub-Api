# FreeReels Subtitle & Video Quality Analysis

## Subtitle Support

### Availability
✅ **25 languages** available per episode via `subtitle_list` field in `/drama/info_v2` response.

### Format
- **SRT** (SubRip Text) - standard subtitle format
- **VTT** (WebVTT) - web-optimized format for HTML5 video players

### Languages
| Language | Code | Type | Example URL |
|----------|------|------|-------------|
| Indonesia | id-ID | original | `https://video-v81.mydramawave.com/vt/22100/fc0aba4c-ee4d-4cd6-bf5d-77fe27abd0e2.srt` |
| English | en-US | normal | `https://video-v6.mydramawave.com/vt/22100/5bb7a734-4a27-4838-a312-3f319be2a9a5.srt` |
| Spanish | es-MX | normal | `https://video-v81.mydramawave.com/vt/22100/60232e5e-1da0-4cd3-9388-7f14d26b3a87.srt` |
| Portuguese | pt-PT | normal | `https://video-v81.mydramawave.com/ut/22100/12a68345-0b9f-4045-95fc-8468d5bb574d.srt` |
| German | de-DE | normal | `https://video-v6.mydramawave.com/vt/22100/0d798a5b-0f55-45c4-869b-5041ee1f3e65.srt` |
| French | fr-FR | normal | `https://video-v81.mydramawave.com/vt/22100/0c7315a3-9712-4126-a815-33f29f738c42.srt` |
| Russian | ru-RU | normal | `https://video-v6.mydramawave.com/vt/22100/0c98b027-b4cf-427f-82d3-94021d129709.srt` |
| Italian | it-IT | normal | `https://video-v81.mydramawave.com/vt/22100/68c10926-72a5-45b3-818a-1feb2fb7c245.srt` |
| Turkish | tr-TR | normal | `https://video-v81.mydramawave.com/vt/22100/d3a2f2e7-1cf5-4623-98ed-b83719de58ef.srt` |
| Japanese | ja-JP | normal | `https://video-v81.mydramawave.com/vt/22100/7b5bc522-a2b9-4c82-88d2-b39007959462.srt` |
| Korean | ko-KR | normal | `https://video-v81.mydramawave.com/vt/22100/c704557b-becc-45bf-b664-aae95a9176aa.srt` |
| Thai | th-TH | normal | `https://video-v6.mydramawave.com/vt/22100/dc7da599-4cae-4e81-b8ee-73fde5581b11.srt` |
| Vietnamese | vi-VN | normal | `https://video-v6.mydramawave.com/ut/22100/1_2b16983b-41bd-4325-aecf-708405a3ffd4.srt` |
| Filipino | tl-PH | normal | `https://video-v81.mydramawave.com/vt/22100/95205929-4ea2-4f0d-b775-7888559a7874.srt` |
| Malay | ms-MY | normal | `https://video-v6.mydramawave.com/vt/22100/a03c4fe9-6a53-4316-9b9c-cc2401f9a0fd.srt` |
| Chinese (Traditional) | zh-TW | normal | `https://video-v81.mydramawave.com/vt/22100/d6bf53c0-65fa-44e9-97fe-f833b51b864f.srt` |
| Hindi | hi-IN | normal | `https://video-v6.mydramawave.com/vt/22100/bd08799b-6e66-4c52-8b32-2b04376f156d.srt` |
| Arabic | ar-SA | normal | `https://video-v6.mydramawave.com/vt/22100/1960a970-31ca-4f70-bb2d-4d813a730579.srt` |
| Greek | el-GR | normal | `https://video-v6.mydramawave.com/vt/22100/4336f0b3-ccbe-4149-91b5-a0aff889f8ae.srt` |
| Polish | pl-PL | normal | `https://video-v81.mydramawave.com/vt/22100/5d0b3658-ea20-4497-b19d-536630ee1cce.srt` |
| Bengali | bn-BD | normal | `https://video-v6.mydramawave.com/vt/22100/b657a799-a81f-41a6-ac98-b1af2f463467.srt` |
| Czech | cs-CZ | normal | `https://video-v6.mydramawave.com/vt/22100/f368f8c3-c200-4079-a10e-0d9cd6f4562a.srt` |
| Telugu | te-IN | normal | `https://video-v6.mydramawave.com/vt/22100/700a0027-6152-4410-8ba5-5752152ff218.srt` |
| Tamil | ta-IN | normal | `https://video-v6.mydramawave.com/vt/22100/1b7040c0-b140-4c4d-84f5-b4c806615b02.srt` |
| Romanian | ro-RO | normal | `https://video-v6.mydramawave.com/vt/22100/22b0d79e-98eb-4081-a23c-466d704ef339.srt` |

### CDN Access
Subtitle URLs **do NOT require authentication**. Direct HTTP GET works without OAuth headers.

### Extraction
```python
drama = client._request("GET", "/frv2-api/drama/info_v2", params={"series_id": "eAiS7aYiYQ", "scene": "1"})
episode = drama["info"]["episode_list"][0]

for sub in episode["subtitle_list"]:
    lang = sub["language"]
    srt_url = sub["subtitle"]
    vtt_url = sub["vtt"]
    print(f"{lang}: {srt_url}")
```

---

## Audio Dubbing

### Availability
❌ **NOT AVAILABLE**. Episodes contain single audio track only.

### Evidence
- Field `audio: null` in episode object
- Field `original_audio_language: "en-US"` indicates single English audio track
- HLS master playlist contains only one `AUDIO="default-audio-group"`
- No multi-audio variants like Netflix (`AUDIO="en"`, `AUDIO="es"`, etc.)

### Workaround
None. Audio dubbing not supported. Only subtitle translations available.

---

## Video Quality

### Maximum Resolution
**720p (720x1280 portrait)** for drama "Monster? Aku Terikat dengan Dewi" (series_id: eAiS7aYiYQ).

### Available Resolutions
From `trans_resolution` field: `720x1280,540x960,480x854,360x640,240x426`

| Resolution | Quality Label | Aspect Ratio |
|------------|---------------|--------------|
| 720x1280 | 720p | 9:16 (portrait) |
| 540x960 | 540p | 9:16 (portrait) |
| 480x854 | 480p | ~9:16 (portrait) |
| 360x640 | 360p | 9:16 (portrait) |
| 240x426 | 240p | ~9:16 (portrait) |

### 1080p Availability
❌ **NOT AVAILABLE** for this drama. Maximum is 720p.

**Note:** Drama optimized for mobile vertical viewing. Landscape 1920x1080 equivalent would be 1080x1920 portrait, which is not present.

### Other Dramas
Not tested. Field `trans_resolution` in `/drama/info_v2` response will indicate available resolutions per drama.

### HLS Adaptive Streaming
All resolutions delivered via single HLS master playlist. Video player automatically selects best quality based on network bandwidth.

---

## VIP/Lock Mechanism

### Token Type
**OAuth MD5-based**, NOT JWT.

### Fields Involved
- `locked: true/false` - server-rendered boolean flag
- `unlock: true/false` - whether user has unlocked this episode
- `video_type: "free"` - paradoxically shows "free" even when `locked: true`
- `episode_price: 60` - coin cost to unlock

### Client-Side vs Server-Side
**Server-side flag** with **no CDN enforcement**.

### Bypass
Lock flag does not prevent video URL from being included in API response. CDN does not validate unlock status. See `VIP_BYPASS_ANALYSIS.md` for details.

---

## Summary Table

| Feature | Status | Details |
|---------|--------|---------|
| Subtitle | ✅ YES | 25 languages, SRT+VTT, no auth required |
| Audio Dub | ❌ NO | Single audio track only (en-US) |
| Max Quality | 720p | Portrait format (720x1280) |
| 1080p | ❌ NO | Not available for tested drama |
| Auth Type | OAuth MD5 | Not JWT |
| Lock Enforcement | Client-side only | CDN does not validate |
