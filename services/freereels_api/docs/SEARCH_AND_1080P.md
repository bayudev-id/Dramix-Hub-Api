# FreeReels Search Endpoint & 1080p Availability

## Search Endpoint

### Endpoint
```
POST /frv2-api/search/drama
```

### Request Body
```json
{
  "keyword": "search query",
  "timestamp": "1727974320271",
  "next": null,
  "tab_key": null
}
```

### Response Structure
```json
{
  "page_info": {...},
  "items": [
    {
      "id": "5RFoNNw9lr",
      "name": "Disangka Boneka Seks Kakak Iparku",
      ...
    }
  ],
  "hot_list_style": {...},
  "search_result_style": {...},
  "you_might_like_style": {...}
}
```

### Notes
- `timestamp` is Unix epoch milliseconds (current time)
- `next` is for pagination (null for first page)
- `tab_key` is optional filter (null = all)
- Search is case-insensitive and supports partial matching

---

## 1080p Availability

### Confirmed Drama with 1080p
**Title:** Disangka Boneka Seks Kakak Iparku  
**ID:** `5RFoNNw9lr`  
**Episodes:** 60  
**Resolutions:** `1080x1920,720x1280,540x960,480x854,360x640,240x426`

### Sample Video URLs (Episode 1)
- **H.264 (1080p):** `https://video-v6.mydramawave.com/vt/6d81995b-d228-479e-b0bd-b9867ca914a0/h264-96d55438-3d69-4550-a4a5-106a61e25b91.m3u8`
- **H.265 (1080p):** `https://video-v81.mydramawave.com/vt/6d81995b-d228-479e-b0bd-b9867ca914a0/h265-96d55438-3d69-4550-a4a5-106a61e25b91.m3u8`
- **Indonesian Subtitle:** `https://video-v81.mydramawave.com/ut/24232/1_8f7b58a5-477a-4171-b49b-0e9f11bce1ef.srt`

### Resolution Format
FreeReels uses **portrait mode (vertical video)** for mobile:
- `1080x1920` = 1080p portrait (equivalent to 1920x1080 landscape rotated)
- `720x1280` = 720p portrait
- `540x960` = 540p portrait
- etc.

### 1080p vs 720p
- First tested drama "Monster? Aku Terikat dengan Dewi" only had **720p max**
- Drama "Disangka Boneka Seks Kakak Iparku" has **1080p**
- Resolution availability varies per drama (likely based on upload date/source quality)

---

## Search Python Client

### Basic Search
```python
from freereels_client import FreeReelsClient
import time

client = FreeReelsClient()
client.login_anonymous()

payload = {
    "keyword": "boneka seks",
    "timestamp": str(int(time.time() * 1000)),
    "next": None,
    "tab_key": None
}

result = client._request("POST", "/frv2-api/search/drama", json=payload)

for drama in result.get("items", []):
    print(f"{drama['name']} (ID: {drama['id']})")
```

### Check for 1080p
```python
detail = client._request("GET", "/frv2-api/drama/info_v2", params={
    "series_id": drama_id,
    "scene": "1"
})

episode = detail["info"]["episode_list"][0]
resolution = episode.get("trans_resolution", "")

if "1080" in resolution:
    print(f"1080p available: {episode['external_audio_h264_m3u8']}")
```

---

## API Endpoints Summary

### Search Endpoints (from y9.t interface)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/search/hot_words` | Hot search keywords |
| POST | `/frv2-api/search/drama` | Main search endpoint |
| POST | `/search/suggestion` | Search suggestions |
| POST | `/search/keywords` | Keyword search |
| GET | `/frv2-api/search/trending_searches` | Trending searches |
| POST | `/search/security` | Security check for search |
| GET | `/frv2-api/search/audio-tabs` | Audio tab filters |
| POST | `/search/hot-list-v2` | Hot list v2 |

---

## Files Created
- `src/test_search_drama.py` - Search drama by keyword
- `src/search_variations.py` - Search with multiple query variations
- `src/extract_1080p_drama.py` - Extract 1080p drama details
- `output/1080p_drama_sample.json` - Sample 1080p drama metadata
- `docs/SEARCH_AND_1080P.md` - This documentation
