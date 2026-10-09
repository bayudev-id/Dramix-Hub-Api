# FreeReels API Endpoints Discovery

Berdasarkan analisis static (decompiled APK) dan dynamic analysis (Frida hook), berikut adalah daftar endpoint yang ditemukan:

---

## 🌐 Base URLs

### Primary API
```
https://api.mydramawave.com/
https://apiv2.free-reels.com/
https://video-v1.mydramawave.com/
```

### Video CDN (HLS Streaming)
```
https://video-v1.mydramawave.com/vt/{uuid}/
https://video-v5.mydramawave.com/vt/{uuid}/
https://video-v6.mydramawave.com/vt/{uuid}/
```

### Static Assets
```
https://static-v1.mydramawave.com/
```

### Discovered from JADX Analysis (NetworkDiagnosisViewModel)

**DramaWave Hosts:**
- `api.mydramawave.com` - Main API
- `trace.mydramawave.com` - Analytics/Tracking
- `m.mydramawave.com` - Mobile web
- `video-v1.mydramawave.com` - Video CDN v1
- `video-v5.mydramawave.com` - Video CDN v5
- `video-v6.mydramawave.com` - Video CDN v6
- `static-v1.mydramawave.com` - Static assets

**FreeReels Hosts:**
- `apiv2.free-reels.com` - FreeReels API v2
- `trace.free-reels.com` - FreeReels tracking

**Test Video URLs (HLS):**
```
https://video-v1.mydramawave.com/vt/d2c30405-4f42-4d68-9c33-9ba408c57816/
  ├── h264-ecf3ad0b-73bb-4392-9f02-d8c0b6dcdda2.m3u8
  └── h265-ecf3ad0b-73bb-4392-9f02-d8c0b6dcdda2.m3u8
```

---

## 📺 Theater/Feed Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/v1/theater/feed?tab={tab}&page={n}` | Main feed content |
| GET | `/v1/theater/recommend?source={source}` | Recommended content |
| GET | `/v1/theater/hot_list?type={type}` | Popular/Trending content |
| GET | `/v1/banner/home` | Home banner ads |
| GET | `/v1/coming_soon/list?date_from={}&date_to={}` | Upcoming content |

**Parameters:**
- `tab`: recommend, picks_for_you, popular_choice_hybrid
- `type`: drama, novel
- `source`: home, theater

---

## 🎬 Video/Content Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/v1/video/detail?series_id={}&episode_id={}` | Video detail info |
| POST | `/v1/video/unlock` | Unlock episode |
| GET | `/v1/content/rating?content_id={}` | Content rating/tags |
| GET | `/v1/subtitle/list?video_id={}&lang={}` | Subtitle list |
| GET | `/v1/download/quality?video_id={}` | Download quality options |
| GET | `/v1/actor/popular?page={n}` | Popular actors |

**Unlock Body:**
```json
{
  "episode_id": "E67890",
  "payment_type": "coin",
  "coin_amount": 10
}
```

---

## 👤 User/Wallet Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/user/login` | User login |
| GET | `/v1/user/profile` | User profile |
| POST | `/v1/user/wallet/balance` | Check wallet balance |
| GET | `/v1/user/vip/status` | VIP subscription status |
| GET | `/v1/coupon/list?user_id={}` | User coupons |
| POST | `/v1/coupon/use` | Use coupon |

**Login Body:**
```json
{
  "phone": "+628123456789",
  "otp": "123456",
  "country_code": "ID"
}
```

---

## 🛒 Purchase/Wallet Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/v1/purchase/store/history?page={}&size={}` | Purchase history |
| POST | `/v1/reward/checkin` | Daily check-in reward |
| GET | `/v1/reward/tasks/daily` | Daily tasks list |

---

## 📚 Novel Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/v1/novel/list?category={}&page={n}` | Novel catalog |
| GET | `/v1/novel/chapter?novel_id={}&chapter_id={}` | Chapter content |
| GET | `/v1/novel/unlock?novel_id={}&chapter_id={}` | Unlock chapter |

---

## 📋 MyList Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/v1/mylist?user_id={}&type={}` | User's saved list |
| POST | `/v1/mylist/add` | Add to my list |
| DELETE | `/v1/mylist/remove?content_id={}` | Remove from my list |

**Add Body:**
```json
{
  "content_id": "S12345",
  "content_type": "drama"
}
```

---

## 💬 Comment Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/v1/comment/list?content_id={}&page={}&size={}` | Comment list |
| POST | `/v1/comment/add` | Add comment |

**Add Comment Body:**
```json
{
  "content_id": "S12345",
  "comment": "Great episode!",
  "rating": 5
}
```

---

## 🔍 Search Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/v1/search/query?q={}&type={}&page={n}` | Search content |

**Parameters:**
- `q`: search keyword
- `type`: drama, novel, actor

---

## 📊 Analytics/Config Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/analytics/track` | Track user events |
| GET | `/v1/config/app_version?version={}` | Check app version |

**Analytics Body:**
```json
{
  "event": "video_play",
  "user_id": "12345",
  "content_id": "S12345",
  "episode_id": "E67890",
  "timestamp": 1708675200
}
```

---

## 🎁 Reward Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/v1/reward/novel/list` | Novel rewards |
| GET | `/v1/reward/box/info` | Reward box info |
| POST | `/v1/reward/receive` | Claim reward |
| GET | `/v1/reward/withdrawal/info` | Withdrawal info |

---

## 🔐 Common Headers

```
Authorization: Bearer {jwt_token}
Content-Type: application/json
User-Agent: FreeReels/{version} (Android {os_version})
X-Device-Id: {device_id}
```

---

## 📦 Response Format

### Success Response
```json
{
  "code": 0,
  "message": "success",
  "data": {
    ...
  }
}
```

### Error Response
```json
{
  "code": {error_code},
  "message": "{error_message}",
  "data": null
}
```

---

## 🎯 Repository Classes (Smali)

Lokasi di decompiled APK:
```
smali/com/dramawave/service/api/repository/
```

Found repository files:
- `TheaterRepository.smali`
- `VideoRepository.smali`
- `UserRepository.smali`
- `NovelRepository.smali`
- `PurchaseRepository.smali`
- `Q2.smali`, `R2.smali`, `X2.smali` (numbered repositories)
- `A0.smali` - `R0.smali` (additional repositories)

---

## 🔍 How to Find More Endpoints

### 1. Run Frida Hook
```bash
frida -U -f com.freereels.app -l frida_hook.js --no-pause
```

### 2. Search Decompiled APK
```bash
# Search for URL patterns
grep -r "https://" smali/ | grep -v ".jpg\|.png"

# Search for API endpoints
grep -r "/v1/" smali/ | head -50
```

### 3. Check Network Security Config
```
res/xml/network_security_config.xml
```
Allows cleartext traffic → Can use HTTP proxy (Burp/Mitmproxy)

---

## 📝 Notes

1. **Authentication**: Most endpoints require `Authorization: Bearer {token}` header
2. **Rate Limiting**: Some endpoints may have rate limits
3. **Region Lock**: Content may be region-specific
4. **Version**: API version is `/v1/` - may change in future versions

---

**Last Updated**: 2026-02-23  
**App Version**: FreeReels v2.1.91 (200191001)  
**Framework**: DramaWave
