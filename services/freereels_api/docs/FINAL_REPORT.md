# FreeReels API Reverse Engineering - Final Report

## Executive Summary

Berhasil melakukan reverse engineering lengkap API FreeReels (DramaWave) short-drama streaming Android app dengan pencapaian:

✅ **Full Independence** - Sistem tidak memerlukan device fisik, auto-generate OAuth via anonymous login  
✅ **Response Decryption** - Ekstraksi AES-128-CBC keys dari native library `libdwguard.so` untuk decrypt encrypted responses  
✅ **Video Extraction** - HLS video URLs dan multi-language subtitles dapat diekstrak langsung dari API  
✅ **120+ API Endpoints** - Complete API surface mapping dari Retrofit interfaces  

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│  FreeReelsClient (Python)                               │
├─────────────────────────────────────────────────────────┤
│  1. Anonymous Login                                     │
│     - Generate device_id (UUID)                         │
│     - Compute sign = MD5(secret + device_id)            │
│     - POST /anonymous/login                             │
│     - Store oauth_token + oauth_secret                  │
│                                                         │
│  2. OAuth Signature (All Requests)                      │
│     - sig = MD5(secret + "&" + oauth_secret)            │
│     - Header: oauth_signature={sig},oauth_token={tok}   │
│                                                         │
│  3. Auto-Decrypt Responses                              │
│     - Check header x-decry: 1                           │
│     - AES-128-CBC decrypt with extracted native keys    │
│     - Format: Base64(IV || ciphertext)                  │
│                                                         │
│  4. Video Extraction                                    │
│     - GET /drama/info_v2                                │
│     - Extract external_audio_h264_m3u8 per episode      │
│     - Download via ffmpeg (no DRM, no auth required)    │
└─────────────────────────────────────────────────────────┘
```

## Key Components

### 1. Authentication
**File:** `src/freereels_client.py`, `src/auth.py`

**Anonymous Login Algorithm:**
```python
device_id = uuid4().hex[:16]
sign = MD5("8IAcbWyCsVhYv82S2eofRqK1DF3nNDAv" + device_id)
POST /frv2-api/anonymous/login
  Body: {"device_id": device_id, "device_name": "...", "sign": sign}
  Response: {"auth_key": oauth_token, "auth_secret": oauth_secret}
```

**OAuth Signature (All Subsequent Requests):**
```python
signature = MD5("8IAcbWyCsVhYv82S2eofRqK1DF3nNDAv&" + oauth_secret)
Header: Authorization: oauth_signature={sig},oauth_token={token},ts={ms}
```

**Critical Detail:** `/anonymous/login` adalah SATU-SATUNYA endpoint yang tidak memerlukan `Authorization` header.

### 2. Response Decryption
**Files:** `native/libdwguard.so`, `src/freereels_client.py`

**Native Library Analysis:**
- Binary: ARM64 ELF (20 KB)
- Anti-tampering: TracerPid check (kills process if debugger attached)
- APK signature validation: SHA-256 hash whitelist

**Extracted AES Keys:**
```python
KEY_FLAVOR_1 = b"3sa9Kx7mQu3Ls8Wd"  # Offset 0x13c0, primary
KEY_FLAVOR_2 = b"79psatnvfgktswba"  # Offset 0x13d0, fallback
```

**Cipher Details:**
- Algorithm: AES-128-CBC
- Format: `Base64(IV[16] || AES-CBC-Encrypt(plaintext + PKCS7-padding))`
- Detection: HTTP header `x-decry: 1`
- Disassembly evidence: ARM64 instructions at `0x3df8-0x3e24` show XOR with previous block (CBC mode signature)

**Decryption Implementation:**
```python
def decrypt_native_response(base64_cipher: str) -> str:
    raw = base64.b64decode(base64_cipher)
    iv = raw[:16]
    ciphertext = raw[16:]
    cipher = AES.new(b"3sa9Kx7mQu3Ls8Wd", AES.MODE_CBC, iv)
    decrypted = cipher.decrypt(ciphertext)
    return unpad_pkcs7(decrypted).decode("utf-8")
```

### 3. Video Extraction
**Files:** `docs/VIDEO_EXTRACTION_SPEC.md`, `src/video_downloader.py`

**Discovery:** Video HLS URLs tersedia langsung di response `/drama/info_v2` tanpa memerlukan endpoint `/drama/download` terpisah.

**Response Structure:**
```json
{
  "data": {
    "info": {
      "name": "Drama Title",
      "episode_count": 58,
      "episode_list": [
        {
          "id": "3e7Ltchsvg",
          "index": 1,
          "external_audio_h264_m3u8": "https://video-v6.mydramawave.com/vt/{uuid}/h264-{uuid}.m3u8",
          "external_audio_h265_m3u8": "https://video-v6.mydramawave.com/vt/{uuid}/h265-{uuid}.m3u8",
          "subtitle_list": [...],
          "unlock": true,
          "duration": 158
        }
      ]
    }
  }
}
```

**Video Format:**
- HLS master playlist (`.m3u8`)
- No DRM/encryption on segments
- No authentication required at CDN level
- Resolution variants: 720p, 540p, 480p, 360p, 240p
- Multi-language subtitles (SRT + VTT format)

**Download Command:**
```bash
ffmpeg -i "https://video-v6.mydramawave.com/vt/{uuid}/h264-{uuid}.m3u8" -c copy output.mp4
```

### 4. API Surface
**File:** `docs/API_ENDPOINTS_COMPLETE.md`

**Endpoint Categories:**
- Drama info & playback: `/drama/*` (28 endpoints)
- User & auth: `/user/*`, `/anonymous/login` (15 endpoints)
- VIP & payment: `/wallet/*`, `/vip/*` (18 endpoints)
- Welfare & rewards: `/welfare/*` (24 endpoints)
- Homepage & feed: `/homepage/*` (12 endpoints)
- Search: `/search/*` (8 endpoints)
- Comments & social: `/content/*` (15 endpoints)

**Total:** 120+ documented endpoints

## Files Created

### Documentation
| File | Description |
|------|-------------|
| `docs/ANONYMOUS_LOGIN_SPEC.md` | Anonymous login algorithm & sign computation |
| `docs/RESPONSE_DECRYPTION_SPEC.md` | Native decryption reverse engineering |
| `docs/VIDEO_EXTRACTION_SPEC.md` | HLS video URL extraction guide |
| `docs/API_ENDPOINTS_COMPLETE.md` | Complete API surface map (120+ endpoints) |

### Implementation
| File | Description |
|------|-------------|
| `src/auth.py` | OAuthSigner class (MD5 signature + header builder) |
| `src/freereels_client.py` | Main API client with auto-login, auto-decrypt, 120+ endpoints |
| `src/video_downloader.py` | Bulk video + subtitle downloader (ffmpeg-based) |

### Analysis Tools
| File | Description |
|------|-------------|
| `src/analyze_so.py` | ELF string extractor for native library |
| `src/disasm_arm64.py` | ARM64 disassembler using Capstone |
| `src/disasm_key.py` | AES key location finder in binary |
| `native/libdwguard.so` | Extracted native crypto library (20 KB) |

### Test Scripts
| File | Description |
|------|-------------|
| `src/test_independence.py` | Full chain test (login → profile → homepage → video) |
| `src/test_anonymous_login.py` | Standalone anonymous login verification |
| `src/test_decrypt_live.py` | Live encrypted response decryption test |
| `src/test_download.py` | Video URL extraction test |

## Verification Evidence

### 1. Anonymous Login
```
[OK] Logged in as Tamu (ID: 75913951999)
     Token: 8ZBQ3RQTJq...3XQzC
```

### 2. OAuth Signature
```
[OK] Profile API response: {"name": "Guest", "user_id": "75913951999"}
```

### 3. Response Decryption
```
[*] Encrypted response detected (x-decry=1)
[OK] Decryption successful!
     Plaintext: {"code":200,"data":{"info":{"name":"Monster?...
```

### 4. Video Extraction
```
Drama: Monster? Aku Terikat dengan Dewi
Episodes: 58
HLS URL: https://video-v6.mydramawave.com/vt/d81b16e0-e664-49dc-82af-b96c03fdb50e/h264-...m3u8
Subtitles: 25 languages
```

## Technical Highlights

### Native Library Reverse Engineering
**Challenge:** Android app uses Cronet (libsscronet.so) yang bypass system proxy, membuat Burp Suite tidak bisa intercept traffic.

**Solution:** 
1. Frida SSL pinning bypass untuk OkHttp layer
2. Static analysis dengan Android-Reverse-IDE untuk mapping Retrofit interfaces
3. Extract `libdwguard.so` dari `split_config.arm64_v8a.apk`
4. Disassemble ARM64 binary dengan Capstone untuk locate AES keys

**Key Discovery:**
```asm
; Function 0x3974 - AES key selection by flavor
0x00003984:  adrp       x8, #0x1000
0x00003988:  ldr        q0, [x8, #0x3d0]   ; Load 16-byte key from offset 0x13d0
0x0000398c:  str        q0, [x0]           ; Store to key buffer
```

Offset `0x13c0` berisi string `"3sa9Kx7mQu3Ls8Wd79psatnvfgktswba+~"` — key flavor 1 = first 16 bytes, flavor 2 = next 16 bytes.

### Anti-Tampering Bypass
`libdwguard.so` mendeteksi Frida attach via TracerPid check. Setiap kali `kahlo_jobs_start` dipanggil, proses di-kill oleh system (SIG 9).

**Workaround:** Static analysis tanpa runtime instrumentation. Extract binary dari device dan analyze offline dengan disassembler.

### Encryption Format Discovery
Ciphertext length 225 bytes (tidak kelipatan 16) membuktikan bukan AES-CBC standar. Disassembly menunjukkan:
```asm
0x3d6c:  sub   x24, x27, #0x10    ; length - 16 = actual ciphertext
0x3df0:  ldr   q1, [x21]          ; load first 16 bytes = IV
```
Format: **Prepended IV** (16 bytes pertama adalah IV, sisanya ciphertext).

## Limitations & Future Work

### Current Limitations
1. **VIP/Unlock Mechanism:** Belum dianalisis karena semua drama yang dites fully unlocked untuk guest account
2. **Payment Flow:** Endpoint `/pay/*` belum dites (requires payment credentials)
3. **Ad-Based Unlock:** Endpoint `/ad/*` dan `/advertise/*` belum diverifikasi (requires ad provider integration)

### Recommended Next Steps
1. **Test dengan akun paid/VIP** untuk mapping premium features
2. **Analyze DRM protection** (jika ada) untuk premium content
3. **Automate bulk extraction** dengan rate limiting untuk avoid detection
4. **Build web dashboard** untuk browsing & streaming via Python backend

## Usage Examples

### Basic Authentication & API Call
```python
from freereels_client import FreeReelsClient

client = FreeReelsClient()
client.login_anonymous()

profile = client._request("GET", "/frv2-api/user/profilev2")
print(f"User: {profile['name']}")
```

### Video Download
```bash
python video_downloader.py eAiS7aYiYQ --max-episodes 5 --codec h264
```

### Search & Extract
```python
search = client._request("POST", "/frv2-api/search/drama", 
    json={"keyword": "love", "timestamp": "1700000000000"})

for drama in search["items"][:5]:
    print(f"{drama['name']} - {drama['id']}")
```

## Security Considerations

### For Research Use Only
Sistem ini dibuat untuk:
- Educational reverse engineering
- API documentation
- Security research

**Tidak untuk:**
- Commercial redistribution
- DRM circumvention for piracy
- Terms of service violation

### Rate Limiting
API tidak memiliki rate limiting strict, namun recommended:
- Max 10 requests/second per account
- Use exponential backoff on 429 errors
- Rotate device_id untuk avoid pattern detection

### Legal Compliance
Video content dilindungi copyright. Ekstraksi untuk personal backup legal di beberapa yurisdiksi, namun redistribution/monetization melanggar hukum.

## Skills Applied
- **apk-reverse:** Native library ARM64 disassembly, AES key extraction, anti-tampering analysis
- **incremental-implementation:** Auto-decrypt integration ke API client
- **source-driven-development:** Retrofit interface mapping untuk API endpoint discovery

## Conclusion

Project berhasil mencapai **full independence** dari device fisik. Sistem dapat:
1. ✅ Login otomatis via guest mode
2. ✅ Auto-generate OAuth credentials
3. ✅ Decrypt encrypted responses
4. ✅ Extract video URLs & subtitles
5. ✅ Download content via ffmpeg

**Total work:** 8 dokumentasi, 7 implementasi scripts, 4 test utilities, 1 native binary extraction & analysis.

**Next milestone:** VIP/unlock mechanism analysis (requires paid account or locked drama samples).

---

**Date:** 2026-10-04  
**App Version:** 2.4.91  
**Package:** com.freereels.app  
**API Base:** https://apiv2.free-reels.com
