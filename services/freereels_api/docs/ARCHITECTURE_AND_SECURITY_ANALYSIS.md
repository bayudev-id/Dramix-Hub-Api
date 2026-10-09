# FreeReels / DramaWave - Architecture & Security Analysis

## 1. Executive Summary

FreeReels (DramaWave) adalah aplikasi streaming short-drama berbasis Android. Analisis reverse engineering mengungkap arsitektur API, mekanisme otentikasi, enkripsi native, dan kelemahan mendasar dalam penegakan kontrol akses konten berbayar (VIP).

**Temuan Kunci:**
1. **Otentikasi:** Menggunakan OAuth 1.0a-like HMAC-MD5 via anonymous login (tanpa registrasi).
2. **Kriptografi:** Respons API terenkripsi AES-128-CBC dengan key tersimpan di library native `libdwguard.so` (di-extract via ARM64 disassembly).
3. **VIP Bypass:** Server mengembalikan URL video HLS untuk **seluruh episode** (termasuk episode berbayar) di respons `/drama/info_v2`. Penegakan VIP hanya terjadi di level UI aplikasi (client-side), memungkinkan akses penuh ke konten premium tanpa autentikasi berbayar.
4. **CDN:** Media streaming dihosting di domain terpisah (`mydramawave.com`) tanpa autentikasi level CDN.

---

## 2. Authentication Flow

### Anonymous Login
```
Client                          Server
  |                               |
  |--- POST /anonymous/login ---->|  Headers: app-name, app-version, device-id
  |    (device_id, sign)          |  sign = MD5("8IAcbWyCsVhYv82S2eofRqK1DF3nNDAv" + device_id)
  |                               |
  |<-- 200 OK --------------------|  Returns: auth_key, auth_secret, user_id
  |    (auth_key, auth_secret)    |
```

### Authenticated Request
```
Client                          Server
  |                               |
  |--- GET /drama/info_v2 ------->|  Authorization: oauth_signature={sig},oauth_token={auth_key},ts={ts}
  |    (with OAuth header)        |  sig = MD5("8IAcbWyCsVhYv82S2eofRqK1DF3nNDAv&" + auth_secret)
  |                               |
  |<-- 200 OK (Encrypted) --------|  Headers: x-decry: 1
  |    (Base64 AES-CBC data)      |
```

---

## 3. Cryptographic Implementation

Respons dari endpoint tertentu dienkripsi menggunakan AES-128-CBC.

### Key Derivation
- Key diekstrak dari fungsi native di `libdwguard.so` pada offset `0x13c0` dan `0x13d0`:
  - **Flavor 1:** `3sa9Kx7mQu3Ls8Wd` (16 bytes)
  - **Flavor 2:** `79psatnvfgktswba` (16 bytes)

### Ciphertext Structure
```
+------------------+-----------------------------------------------+
|  IV (16 bytes)   |  AES-128-CBC Ciphertext + PKCS#7 (N*16 bytes) |
+------------------+-----------------------------------------------+
\------------------------------------------------------------------/
                         Base64 Encoded
```

### Decryption Routine
1. Decode base64 string
2. Extract byte 0–15 sebagai IV
3. Decrypt byte 16–end menggunakan AES-128-CBC dengan salah satu flavor key
4. Strip PKCS#7 padding
5. Parse UTF-8 JSON

---

## 4. Video Delivery Architecture

```
+-------------------------+
|     FreeReels App       |
+-------------------------+
       |            |
       | API        | HLS Stream (Direct)
       v            v
+-------------+  +----------------------------+
| API Server  |  | Akamai / Cloudflare CDN    |
| apiv2...com |  | *.mydramawave.com          |
+-------------+  +----------------------------+
                        |
                        v
                 +--------------+
                 | Video Master |
                 | Playlist     |
                 | (.m3u8)      |
                 +--------------+
```

- Master playlist menyediakan multi-bitrate HLS (240p hingga 720p HD vertikal).
- Menggunakan codec video terpisah: H.264 (`external_audio_h264_m3u8`) dan H.265/HEVC (`external_audio_h265_m3u8`).
- Dilengkapi hingga 25 track subtitle WebVTT dan SRT multi-bahasa.

---

## 5. Security Vulnerability: Insecure Direct Object Reference / VIP Bypass

### Deskripsi
Server API menyertakan URL streaming lengkap untuk semua episode di respons `/drama/info_v2`, terlepas dari status kepemilikan atau langganan akun pengguna.

```json
{
  "code": 200,
  "data": {
    "info": {
      "name": "Monster? Aku Terikat dengan Dewi",
      "free": true,
      "free_start": 0,
      "free_end": 10,
      "episode_list": [
        {
          "id": "3e7Ltchsvg",
          "name": "Episode 1",
          "external_audio_h264_m3u8": "https://video-v6.mydramawave.com/.../h264.m3u8"
        },
        {
          "id": "DMK8YTdylS",
          "name": "Episode 58 (VIP)",
          "external_audio_h264_m3u8": "https://video-v6.mydramawave.com/.../h264.m3u8"
        }
      ]
    }
  }
}
```

### Mekanisme Penegakan
- **Server:** Tidak melakukan pemfilteran array `episode_list`. URL langsung diisi untuk episode 1 hingga episode terakhir.
- **Client UI:** Aplikasi memeriksa indeks episode terhadap nilai `free_end` (misal: 10). Jika `index > free_end`, tombol di-render dengan status terkunci dan menampilkan dialog pembelian koin.
- **CDN:** Server media tidak memvalidasi session, cookie, maupun signed query parameters.

### Dampak
Aktor mana pun yang memiliki kemampuan mengirim request HTTP dapat mengambil seluruh episode drama (termasuk konten berbayar) hanya dengan akun anonymous guest.

---

## 6. Rekomendasi Remediasi

### Bagi Penyedia Layanan (FreeReels)
1. **Server-Side Filtering:** Kosongkan field `external_audio_*` untuk episode di luar rentang `free_end` jika pengguna belum membeli episode tersebut.
2. **Dedicated Playback Endpoint:** Pisahkan metadata drama dari link streaming. Buat endpoint `/drama/playback_token` yang memvalidasi hak akses sebelum menerbitkan URL.
3. **Signed CDN URLs:** Gunakan signed URL dengan waktu kadaluarsa singkat (misal: 15 menit) menggunakan token HMAC pada URL CDN (Cloudflare Token Authentication / Akamai EdgeAuth).
4. **Rotasi Native Key:** Hindari hardcoding AES key statis pada native library tanpa lapisan obfuscation atau key derivation berbasis session.

---

## 7. Artifact Deliverables

| Path | Deskripsi |
|---|---|
| `src/api_proxy_v2.py` | FastAPI server & testing playground (responsive UI) |
| `src/freereels_client.py` | Python SDK (auth, decrypt, endpoint wrapper) |
| `src/download_videos.py` | Proof-of-concept HLS stream downloader |
| `docs/API_ENDPOINTS_COMPLETE.md` | Katalog 120+ endpoint hasil analisis |
| `docs/RESPONSE_DECRYPTION_SPEC.md` | Spesifikasi AES-128-CBC native decryption |
| `docs/VIP_BYPASS_PROOF.md` | Laporan teknis kerentanan akses VIP |
| `docs/CATEGORIES_AND_TABS.md` | Pemetaan kategori & homepage tabs |
