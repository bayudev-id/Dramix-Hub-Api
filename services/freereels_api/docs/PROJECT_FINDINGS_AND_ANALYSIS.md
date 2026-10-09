# FreeReels API Reverse-Engineering: Findings & Architecture Documentation

Dokumen ini merekonstruksi dan merangkum seluruh temuan teknis dari riset reverse engineering aplikasi **FreeReels** (DramaWave white-label) pada Android.

---

## 1. Executive Summary & Status Terakhir

* **Status Akses Data:**
  - **Homepage / Tab Feeds (`/homepage/v2/tab/index`):** ✅ **BERJALAN (Public/No-Auth)**. Bisa ditarik langsung tanpa signature.
  - **Video Streaming (HLS m3u8):** ✅ **TERBUKA**. URL `.m3u8` dan subtitle `.srt` di CDN tidak memiliki token expiry pendek atau enkripsi DRM.
  - **Endpoint Terotentikasi (Rank, Wallet, Follow, Detail Episode Berbayar):** ⚠️ **TERKUNCI / 401**. Membutuhkan pembuatan tanda tangan digital (`oauth_signature` dan `sign`) secara dinamis.
* **Bottleneck Utama:**
  - Riset terdahulu belum menemukan implementasi asli algoritma pembentukan signature (apakah HMAC-SHA1, SHA256, atau RSA) di level native lib / bytecode DEX.
  - Skrip lama mengandalkan token capture statis yang kini telah kadaluarsa.

---

## 2. Infrastruktur & Base URL

* **Main API v2:** `https://apiv2.free-reels.com` (Prefix: `/frv2-api`)
* **Tracking & Analytics:** `https://trace.free-reels.com`
* **Static Asset CDN (Cover/Images):** `https://static-v1.mydramawave.com`
* **Video Streaming CDN (HLS):**
  - `https://video-v6.mydramawave.com/vt/{uuid}/h264-{uuid}.m3u8`
  - `https://video-v81.mydramawave.com/vt/{uuid}/h265-{uuid}.m3u8`
  - Varian lain: `video-v1`, `video-v5`, `video-v8`
* **Legacy DramaWave Host:** `api.mydramawave.com`, `trace.mydramawave.com`

---

## 3. Identitas Perangkat & Kredensial Captured

Data hasil capture environment riset sebelumnya:

| Parameter | Nilai Hasil Capture | Keterangan |
|---|---|---|
| `user_id` | `102836515` / `26326148095` | User ID guest/login |
| `AUTH_KEY` / `oauth_token` | `IsSG5rKFz7kfafVlqS8Ubq0JgT4N0a69` | Token OAuth aplikasi |
| `device-id` / `device_hash` | `775eddf9b8392d6b` | Android Settings Secure ID |
| `gaid` | `784b504c-b5fe-4e4a-b1ba-880c3a78ef61` | Google Advertising ID |
| `appsflyer-id` | `1771777699791-1023003935210107517` | SDK Tracker ID |
| `country` / `language` | `ID` / `id-ID` | Region Indonesia |
| `app-version` | `2.2.00` | Versi APK target |
| `Captured oauth_signature` | `edc1ec44568756ef6a23526dfbd089b1` | MD5/SHA1 static dump |
| `Captured sign` | `fkb7tCW63BTpzQcd9+UIY0oL/ZM=` | Base64 HMAC/SHA digest |

---

## 4. Analisis Skema Autentikasi (2-Layer Header)

Request terproteksi memerlukan dua header spesifik:

1. **Header `Authorization`:**
   ```http
   Authorization: oauth_signature={oauth_signature},oauth_token={AUTH_KEY},ts={epoch_ms}
   ```
2. **Header `sign`:**
   ```http
   sign: {base64_encoded_signature}
   ```

### Hipotesis Eksperimen yang Gagal:
1. `freereels_final.py`: Formula HMAC-SHA1 dengan secret `a1d40a30e38a6b19` dan payload `ts + auth_key + user_id` → Menghasilkan **401 Unauthorized**.
2. `fetch_rank_real_fixed.py`: Formula SHA1 biasa → Menghasilkan **401 Unauthorized**.
3. `freereels_sn_generator.py`: Formula placeholder SHA256 string → Ditolak server.

**Kesimpulan Autentikasi:** Algoritma `sign` sesungguhnya dihitung dari kombinasi *Query Params + Body + Timestamp + Secret Key* yang ditanam pada class Java (`HouseBuilder` / Network Interceptor) atau pada library C/C++ native (`.so`).

---

## 5. Inventaris Endpoint API

### A. Public / Feed (Berfungsi Tanpa Auth)
* `GET /frv2-api/homepage/v2/tab/index`
  - Parameter: `tab_key` (505 = New, 503 = Popular, 501 = Male, 504 = Female, 506 = Coming Soon), `position_index=10000`, `rec_trigger=1`
  - Response: Daftar modul drama, judul, cover, tags, dan list episode awal.

### B. Endpoint Terproteksi
* `POST /frv2-api/homepage/v2/rank`
  - Body: `{"rank_type": "daily", "page_num": 1, "page_size": 20}`
* `GET /frv2-api/video/v2/detail`
  - Parameter: `series_key={key}`
* `GET /frv2-api/video/v2/sources`
  - Parameter: `series_key={key}&episode_key={id}`
* `GET /frv2-api/content/message/unread`
* `POST /frv2-api/popup/banner/list`
* `GET /frv2-api/user/risk/check`
* `GET /frv2-api/wallet/my`
* `GET /frv2-api/drama/v3/follow_list`

---

## 6. Rencana Kerja untuk "New Method"

Untuk melanjutkan pengembangan metode baru:
1. **Dekomposisi APK via JADX MCP / Android-Reverse-IDE:**
   - Cari kelas yang menambahkan header `sign` dan `Authorization` pada OkHttp client (cari string `oauth_signature` atau `sign` di JADX).
   - Tentukan apakah signature dihasilkan di Java atau memanggil JNI (`System.loadLibrary`).
2. **Hooking Dinamis Runtime (Frida + Burp Suite):**
   - Kaitkan Frida ke method interceptor OkHttp saat melakukan request `/homepage/v2/rank` untuk mencatat *exact plaintext inputs* sebelum di-hash.
3. **Implementasi Python Signer yang Akurat:**
   - Mereplikasi formula hashing agar client Python bisa generate signature valid kapan saja secara mandiri.
