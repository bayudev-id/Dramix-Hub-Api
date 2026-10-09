# 🎬 FreeReels API - Kesimpulan Akhir

**Tanggal**: 2026-02-23  
**Status**: ✅ **ENDPOINT BERHASIL DITEMUKAN**  
**Status API**: ✅ **BEKERJA TANPA AUTH** (untuk homepage)

---

## 📋 **RINGKASAN EKSEKUTIF**

Dari serangkaian percobaan dengan **Frida hooking** dan **reverse engineering**, kami berhasil:

1. ✅ **Menemukan Base URL API**: `https://apiv2.free-reels.com`
2. ✅ **Menemukan API Prefix**: `/frv2-api`
3. ✅ **Menemukan Endpoint Homepage**: `/frv2-api/homepage/v2/tab/index`
4. ✅ **Menemukan Parameter Query**: `tab_key`, `position_index`, `rec_trigger`
5. ✅ **Mendapatkan Response Data**: Drama list dengan video URLs dan subtitles
6. ✅ **Menemukan Video Stream URLs**: HLS (.m3u8) format
7. ✅ **Menemukan Subtitle URLs**: Multi-language (ID, EN, ES, PT, dll)

---

## 📡 **ENDPOINT YANG DITEMUKAN**

### **Base URL:**
```
https://apiv2.free-reels.com
```

### **API Prefix:**
```
/frv2-api
```

### **Homepage Endpoint:**
```http
GET /frv2-api/homepage/v2/tab/index
```

### **Full URL dengan Parameters:**
```http
GET https://apiv2.free-reels.com/frv2-api/homepage/v2/tab/index?tab_key=505&position_index=10000&rec_trigger=1
```

### **Query Parameters:**
| Parameter | Value | Description |
|-----------|-------|-------------|
| `tab_key` | `505`, `503`, `516`, dll | Tab identifier |
| `position_index` | `10000` | Pagination offset |
| `rec_trigger` | `1` | Recommendation trigger |

### **Headers:**
```http
Host: apiv2.free-reels.com
Accept: application/json
```

**Catatan**: Endpoint homepage **TIDAK memerlukan authentication**!

---

## 📊 **RESPONSE STRUCTURE**

### **Response JSON:**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      {
        "key": "udXSAq8pXQ",
        "title": "Dikhianati Darah Daging Sendiri(Sulih Suara)",
        "cover": "https://static-v1.mydramawave.com/vt/prod/cover/...",
        "desc": "Chen Fan, bos Grup Shanhai yang pensiun...",
        "tag": ["Gratis", "Dubbing"],
        "series_tag": ["Drama", "Tragedi", "Balas Dendam"],
        "content_tags": ["Balas Dendam", "Miskin Jadi Kaya"],
        "episode_count": 62,
        "follow_count": 14997,
        "view_count": 0,
        "episode_info": {
          "id": "v3J9fg55Ee",
          "name": "Dikhianati Darah Daging Sendiri(Sulih Suara)",
          "cover": "https://static-v1.mydramawave.com/vt/video/cover/episode/...",
          "video_url": "",
          "m3u8_url": "",
          "external_audio_h264_m3u8": "https://video-v6.mydramawave.com/vt/.../h264-....m3u8",
          "external_audio_h265_m3u8": "https://video-v6.mydramawave.com/vt/.../h265-....m3u8",
          "subtitle_list": [
            {
              "language": "id-ID",
              "type": "original",
              "subtitle": "https://video-v6.mydramawave.com/vt/.../subtitle.srt",
              "display_name": "Indonesia"
            },
            {
              "language": "en-US",
              "type": "normal",
              "subtitle": "https://video-v6.mydramawave.com/vt/.../subtitle.srt",
              "display_name": "Inggris"
            }
          ],
          "region": null,
          "audio": ["en-US", "zh-CN", "zh-TW", "ja-JP", "ko-KR", ...],
          "original_audio_language": "zh-CN",
          "index": 1,
          "unlock": true,
          "h5_available": false,
          "duration": 198,
          "episode_price": 1,
          "video_type": "free",
          "new": false,
          "update_time": 1767774603,
          "user_unlocked": false,
          "serialize_pub_status": 0,
          "highlight_pub_status": 0,
          "is_blooper": false,
          "trans_resolution": "1080x1920,720x1280,540x960,480x854,360x640"
        },
        "link_type": 1,
        "link": "freereels://freereels.app/detail?id=udXSAq8pXQ",
        "r_info": {...},
        "free": true,
        "free_start": 1760580000,
        "free_end": 2050675200,
        "vip_type": 0,
        "style": 4,
        "pay_index": 8,
        "orientation": 1,
        "resource_type": 1
      }
    ],
    "page_info": {
      "next": "offset=70&position_index=10000",
      "has_more": true
    }
  }
}
```

---

## 🎬 **CONTOH DRAMA YANG DIDAPAT**

| No | Title | Episodes | Follows | Type |
|----|-------|----------|---------|------|
| 1 | Dikhianati Darah Daging Sendiri | 62 eps | 14,997 | Drama |
| 2 | Ayah Anakku Ternyata Serigala? | 77 eps | 37,003 | Fantasy |
| 3 | Kericuhan Pesta Pertunangan | 69 eps | 4,540 | Drama |
| 4 | Lulus Masa Percobaan, Hamil oleh Bosku | 62 eps | 50,935 | Romance |
| 5 | Usai Ditolak, Ia Menyingkap Jati Dirinya | 62 eps | 40,281 | Romance |
| 6 | Cinta Rahasia Tuan CEO | 81 eps | 1,118 | Romance |
| 7 | Ibu, Tolong Sayangi Aku | 37 eps | 1,958 | Drama |
| 8 | Ahli Waris Merebut Kembali Rumahnya | 64 eps | 7,147 | Drama |
| 9 | Dari Petani Jadi Suami Sang Permaisuri | 74 eps | 60,165 | Fantasy |
| 10 | Kali Ini, Akulah Sang Antagonis | 58 eps | 20,095 | Drama |

---

## 🎥 **VIDEO STREAM URLS**

### **Format HLS (.m3u8):**
```
https://video-v6.mydramawave.com/vt/{uuid}/h264-{uuid}.m3u8
https://video-v6.mydramawave.com/vt/{uuid}/h265-{uuid}.m3u8
```

### **Video Quality Options:**
```
1080x1920 (Full HD)
720x1280 (HD)
540x960 (SD)
480x854
360x640
```

### **Subtitle Languages:**
- Indonesian (id-ID)
- English (en-US)
- Spanish (es-MX)
- Portuguese (pt-PT)
- Russian (ru-RU)
- Arabic (ar-SA)
- Hindi (hi-IN)
- Japanese (ja-JP)
- Korean (ko-KR)
- Thai (th-TH)
- Vietnamese (vi-VN)
- Chinese (zh-CN, zh-TW)
- Dan banyak lagi!

---

## 🛠️ **FRIDA HOOK YANG BERHASIL**

### **Script yang Digunakan:**
`capture_homepage_response.js`

### **Hooks yang Berhasil:**
1. ✅ `okhttp3.ResponseBody.string()` - Capture response body
2. ✅ `okhttp3.Request$Builder.build()` - Capture request
3. ✅ Response parsing berhasil
4. ✅ Data extraction berhasil

### **Hooks yang Gagal:**
- ❌ `okhttp3.RealCall.execute()` - Class not found (obfuscated)

---

## ✅ **KESIMPULAN**

### **Yang Berhasil:**
1. ✅ **Base URL API ditemukan**: `https://apiv2.free-reels.com`
2. ✅ **API Prefix ditemukan**: `/frv2-api`
3. ✅ **Homepage endpoint bekerja**: GET `/frv2-api/homepage/v2/tab/index`
4. ✅ **Response data lengkap**: Drama list dengan metadata lengkap
5. ✅ **Video URLs ditemukan**: HLS stream (.m3u8)
6. ✅ **Subtitle URLs ditemukan**: Multi-language
7. ✅ **Frida hook berhasil**: Intercept API calls berhasil

### **Yang Perlu Dilanjutkan:**
1. ⚠️ **Episode endpoint**: Perlu discover endpoint untuk episode detail
2. ⚠️ **Video stream authentication**: Perlu test apakah video URLs perlu auth
3. ⚠️ **Pagination**: Perlu test pagination dengan parameter `next`
4. ⚠️ **Other endpoints**: Explore endpoints lain (search, detail, dll)

---

## 🚀 **NEXT STEPS**

### **1. Test Homepage Endpoint dengan Python:**
```python
import requests

url = "https://apiv2.free-reels.com/frv2-api/homepage/v2/tab/index"
params = {
    "tab_key": "505",
    "position_index": "10000",
    "rec_trigger": "1"
}

response = requests.get(url, params=params)
data = response.json()
```

### **2. Extract Video URLs:**
```python
for item in data['data']['items']:
    episode = item.get('episode_info', {})
    video_url = episode.get('external_audio_h264_m3u8')
    subtitles = episode.get('subtitle_list', [])
    
    print(f"Title: {item['title']}")
    print(f"Video URL: {video_url}")
    print(f"Subtitles: {len(subtitles)} languages")
```

### **3. Test Video Stream:**
```python
# Test play dengan VLC atau requests
video_url = "https://video-v6.mydramawave.com/vt/.../h264-....m3u8"
response = requests.get(video_url)
print(response.text)  # HLS playlist
```

---

## 📝 **CATATAN PENTING**

1. **Homepage endpoint TIDAK perlu authentication** - Ini bagus!
2. **Video URLs adalah HLS (.m3u8)** - Bisa diputar di VLC
3. **Subtitles tersedia dalam banyak bahasa** - Termasuk Indonesia
4. **Video quality bervariasi** - Dari 360p sampai 1080p
5. **Pagination tersedia** - Parameter `next` untuk halaman berikutnya

---

## 🎯 **KESIMPULAN AKHIR**

### **Status: ✅ BERHASIL**

Kami berhasil:
1. ✅ **Menemukan API endpoint** yang bekerja
2. ✅ **Mendapatkan data drama** lengkap dengan metadata
3. ✅ **Mendapatkan video URLs** dalam format HLS
4. ✅ **Mendapatkan subtitle URLs** multi-language
5. ✅ **Frida hook berhasil** intercept API calls

### **Apa yang Bisa Dilakukan:**
1. ✅ **Browse drama** dari homepage
2. ✅ **Get video URLs** untuk streaming
3. ✅ **Download subtitles** dalam berbagai bahasa
4. ✅ **Browse by tab** dengan different tab_key

### **Next Steps:**
1. ⚠️ **Test video streaming** dengan URLs yang didapat
2. ⚠️ **Explore episode endpoints** untuk detail episode
3. ⚠️ **Test pagination** untuk load lebih banyak drama
4. ⚠️ **Explore search endpoint** untuk search drama

---

**Tanggal**: 2026-02-23  
**Status**: ✅ **ENDPOINT BERHASIL DITEMUKAN**  
**Next**: Test video streaming dan explore endpoints lain

---

**Dibuat oleh**: Frida Hook Experiment  
**Tools**: Frida 17.6.2, Python 3.11  
**Status**: ✅ **BERHASIL**
