# JADX Analysis Results - FreeReels v2.1.91

Hasil analisis decompiled APK menggunakan JADX.

---

## 📦 Package Information

**Main Package:** `com.freereels.app`  
**Framework:** `com.dramawave.app`  
**Version:** 2.1.91 (200191001)

---

## 🎯 Key Discovery: NetworkDiagnosisViewModel

**File:** `com/dramawave/feature/profile/diagnosis/viewmodel/NetworkDiagnosisViewModel.kt`

Class ini berisi **hardcoded test endpoints** yang digunakan untuk network diagnosis. Ini adalah sumber utama untuk menemukan semua domain/endpoint yang digunakan aplikasi.

### 📍 Discovered Hosts

#### DramaWave Hosts (builtInTestHosts)
```kotlin
"api.mydramawave.com"           // Main API
"trace.mydramawave.com"         // Analytics/Tracking
"m.mydramawave.com"             // Mobile web
"video-v1.mydramawave.com"      // Video CDN v1
"video-v5.mydramawave.com"      // Video CDN v5
"video-v6.mydramawave.com"      // Video CDN v6
"static-v1.mydramawave.com"     // Static assets
"www.google.com"                // Connectivity test
"www.youtube.com"               // Connectivity test
"www.facebook.com"              // Connectivity test
"www.twitter.com"               // Connectivity test
```

#### FreeReels Hosts (builtInTestHostsFreeReels)
```kotlin
"apiv2.free-reels.com"          // FreeReels API v2
"trace.free-reels.com"          // FreeReels tracking
"m.mydramawave.com"
"video-v1.mydramawave.com"
"video-v5.mydramawave.com"
"video-v6.mydramawave.com"
"static-v1.mydramawave.com"
"www.google.com"
"www.youtube.com"
"www.facebook.com"
"www.twitter.com"
```

### 📺 HLS Test Video URLs (builtInTestVideoUrls)

```kotlin
// H.264 format
"https://video-v1.mydramawave.com/vt/d2c30405-4f42-4d68-9c33-9ba408c57816/h264-ecf3ad0b-73bb-4392-9f02-d8c0b6dcdda2.m3u8"

// H.265/HEVC format
"https://video-v1.mydramawave.com/vt/d2c30405-4f42-4d68-9c33-9ba408c57816/h265-ecf3ad0b-73bb-4392-9f02-d8c0b6dcdda2.m3u8"
```

### 🌐 HLS CDN URLs (HLS_CDN_URLS)

```kotlin
"https://video-v1.mydramawave.com/"
"https://video-v5.mydramawave.com/"
"https://video-v6.mydramawave.com/"
```

---

## 📂 Important Repository Classes

Lokasi: `com/dramawave/service/api/repository/`

### Main Repositories

| Class | Purpose |
|-------|---------|
| `q1.smali` | Profile/User repository |
| `C2800q1.smali` | Profile repository (numbered) |
| `TheaterRepository.smali` | Theater/feed content |
| `VideoRepository.smali` | Video operations |
| `UserRepository.smali` | User operations |
| `NovelRepository.smali` | Novel content |
| `PurchaseRepository.smali` | Purchase/wallet |
| `R2.smali`, `X2.smali` | Additional repositories |
| `A0.smali` - `R0.smali` | Numbered repositories |

### Novel Repository (specific)

Lokasi: `com/dramawave/service/api/repository/novel/`

```
a.smali, b.smali, c.smali, d.smali, e.smali, f.smali
g.smali, h.smali, i.smali, j.smali, k.smali, l.smali
m.smali, n.smali, o.smali, p.smali, q.smali, r.smali
s.smali, t.smali, u.smali, v.smali, w.smali, x.smali
```

---

## 🔍 Other Important Classes

### Network Diagnosis
```
com.dramawave.core.network.diagnosis.
├── HostDiagnosisService.smali
├── HlsDiagnosisService.smali
├── j.smali (HLS result model)
├── m.smali (Host result model)
├── n.smali (Host diagnosis request)
└── q.smali (Diagnosis utilities)
```

### Analytics
```
com.dramawave.shared.analytics.
├── RDEventName$Companion.smali
└── k.smali (Analytics tracker)
```

**Event Names Found:**
- `RD_HLS_STREAM_DIAGNOSIS_RESULT`
- `RD_HOST_DIAGNOSIS_RESULT`

### VIP/Purchase
```
com.dramawave.shared.iap.
├── data/IAPError.smali
├── common/Product.smali
├── dialog/
│   ├── SelectPaymentChannelDialog.smali
│   └── InternalPurchaseDialog.smali
└── business/
```

### Wallet/Payment
```
com.dramawave.feature.profile.wallet.
├── fragment/BaseMemberCenterFragment.smali
├── vm/MemberCenterEvent.smali
└── VipProSubscriptionSuccessDialog.smali
```

### Rewards
```
com.dramawave.feature.reward.
├── benefit/
│   ├── manager/
│   ├── ui/
│   └── viewmodel/BenefitViewModel.smali
├── novel/
│   ├── ui/dialog/
│   └── viewmodel/
└── original/
    ├── PointRewardTabFragment.smali
    └── TaskHelpDialog.smali
```

---

## 🎬 Video/Player Related

### Player Components
```
com.dramawave.shared.player.
├── core/
│   ├── controller/PlayerController.smali
│   ├── manager/
│   │   ├── PlayerControllerCache.smali
│   │   ├── VideoCacheManager.smali
│   │   └── SubtitleCacheManager.smali
│   └── manager/h.smali (VideoCacheManager impl)
├── view/
│   ├── DirectionalVideoPager.smali
│   └── VideoSeekBar.smali
└── databinding/
```

### Video Repository
Found references to:
- Video unlock
- Episode management
- Subtitle handling
- Download quality

---

## 📱 UI/Feature Structure

### Main Features
```
com.dramawave.feature.
├── home/           # Main feed/video player
├── theater/        # Theater mode browsing
├── profile/        # User profile & settings
├── novel/          # Novel reading
├── reward/         # Rewards system
├── mylist/         # Watchlist
├── search/         # Search functionality
├── hotList/        # Trending content
├── actor/          # Actor info
├── comeingsoon/    # Coming soon (note: typo in package name)
├── contenttag/     # Content tags
├── develop/        # Dev tools/debug
├── login/          # Authentication
├── web/            # WebView pages
└── widget/         # Home screen widgets
```

### Theater Adapters
```
com.dramawave.feature.theater.adapter.
├── feedVH/         # Feed view holders
└── headerVH/       # Header view holders
    ├── TripleGridVerticalVH.smali
    └── binder/
```

---

## 🔐 Authentication/Security

### Login/ Auth
```
com.dramawave.feature.login.
├── activity/
│   ├── LoginActivity.smali
│   └── AuthShadowActivity.smali
└── Facebook integration (CustomTabActivity)
```

### Token Management
- JWT Bearer tokens used
- Stored in CommonStore/MMKV
- Refresh mechanism via UserRepository

---

## 📊 Analytics Events

Found in `com.dramawave.shared.analytics.RDEventName`:

```kotlin
// Network Diagnosis
RD_HLS_STREAM_DIAGNOSIS_RESULT
RD_HOST_DIAGNOSIS_RESULT

// Likely events (based on class names)
RD_VIDEO_PLAY
RD_VIDEO_COMPLETE
RD_PURCHASE_SUCCESS
RD_REWARD_CLAIM
RD_CHECKIN
```

---

## 🛠️ Development/Debug Features

### Develop Activity
```
com.dramawave.feature.develop.
├── DevelopActivity.smali
├── DevelopVideoActivity.smali
├── DevelopSeekBarActivity.smali
├── DevelopNotificationActivity.smali
├── DevelopImageActivity.smali
├── DevelopRouterActivity.smali
├── TestUmpActivity.smali
├── TestStringsActivity.smali
└── ad/
    ├── TestAdActivity.smali
    ├── TestNativeAdActivity.smali
    └── TestMetaNativeAdActivity.smali
```

**Note:** These suggest the app has extensive testing features built-in.

---

## 📦 Third-Party Integrations

### Ad Networks
```
- AppLovin (MAX)
- Facebook Audience Network
- Google AdMob
- Unity Ads
- Vungle
- IronSource (via Unity)
- Pangle (ByteDance)
- InMobi
- Fyber (FairBid)
- Moloco
- TaurusX
- BidMachine
- Opera Ads
```

### Analytics/Crash Reporting
```
- Firebase Analytics
- Firebase Crashlytics
- Firebase Performance
- AppsFlyer (attribution)
```

### Payment
```
- Google Play Billing
- Facebook Payment (possibly)
```

### Other SDKs
```
- Ishumei (anti-fraud)
- SafeDk (SDK management)
- Therouter (routing)
- MMKV (key-value storage)
```

---

## 🗄️ Database/Storage

### Room Database
```
com.dramawave.core.db.
├── DBManager.smali
└── dao/
    └── a.smali (Download DAO)
```

### Entity Classes
```
com.dramawave.core.db.entity.
└── SDownloadStateEntity.smali
```

### Key-Value Storage (MMKV)
```
com.dramawave.core.kv.store.
├── CommonStore.smali
├── UserStore.smali
├── H265DowngradeStore.smali
├── NovelAuthStore.smali
└── Property classes (l.smali, p.smali, v.smali, etc.)
```

---

## 🎯 Key Models/Data Classes

### Theater/Feed
```
com.dramawave.shared.models.theater.
└── TheaterDataType.smali  # Content types
```

**Content Types:**
- banner
- operation_banner
- column_horizontal
- column_vertical
- column_vertical_three
- billboard
- recommend
- daily_special_offers
- infinity_three
- coming_soon
- picks_for_you
- feature_hybrid
- popular_choice_hybrid

### Novel
```
com.dramawave.shared.models.
├── Novel.smali
├── NovelItemData.smali
├── Chapter.smali
└── novel/
    ├── NovelInfoBean.smali
    ├── NovelUnlockBean.smali
    └── AuthContentBean.smali
```

### User/Wallet
```
com.dramawave.shared.models.
├── UserInfo.smali
├── wallet/
│   ├── MemberCenterModel.smali
│   ├── VipCenterModel.smali
│   ├── MyCouponBean.smali
│   └── MessageInfo.smali
└── bean/
    ├── PurchaseStoreBean.smali
    └── WalletBean.smali
```

### Video
```
com.dramawave.shared.models.
├── Episode.smali
├── PlayDetail.smali
├── Series.smali
└── VideoDownload.smali
```

---

## 📝 Notes

1. **NetworkDiagnosisViewModel** adalah sumber utama untuk menemukan semua endpoint
2. Aplikasi menggunakan **multiple CDN URLs** untuk video streaming
3. **FreeReels** dan **DramaWave** menggunakan infrastructure yang sama
4. Ada **16+ repository classes** yang kemungkinan berisi API endpoint definitions
5. Aplikasi memiliki **extensive development/debug tools** built-in
6. **H.265 support** tersedia (dengan fallback ke H.264)

---

## 🔍 Next Steps

1. **Hook Repository Classes** dengan Frida untuk capture actual API calls
2. **Monitor NetworkDiagnosisService** execution untuk see live endpoint tests
3. **Decompile more classes** in `com/dramawave/service/api/repository/`
4. **Trace Retrofit service creation** to find base URLs
5. **Analyze OkHttp interceptors** for request/response logging

---

**Analysis Date:** 2026-02-23  
**APK Version:** FreeReels_v2.1.91(200191001)_antisplit.apk  
**Decompiler:** JADX + Apktool
