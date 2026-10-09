# 🔑 FreeReels API - Reverse Engineering Guide

## 📋 Status Saat Ini

### ✅ Yang Sudah Ditemukan:

1. **Base URLs:**
   - `https://apiv2.free-reels.com` ✅
   - `https://trace.free-reels.com` ✅
   - `https://static-v1.mydramawave.com` ✅

2. **Endpoints (dari Frida log):**
   ```
   GET  /homepage/v2/tab/index?tab_key={key}&position_index=10000&rec_trigger=1
   GET  /content/message/unread
   POST /popup/banner/list
   GET  /user/risk/check
   GET  /wallet/my
   GET  /drama/v3/follow_list?series_type={1-4}&next=
   POST /b/frv2_client_track
   ```

3. **Device Info (dari log):**
   ```
   Device ID: 784b504c-b5fe-4e4a-b1ba-880c3a78ef61
   Android ID: 00000000648b8cdc648b8cdc00000000
   Device: Redmi 5 Plus (vince)
   App Version: 2.2.00
   GAID: 784b504c-b5fe-4e4a-b1ba-880c3a78ef61
   ```

### ❌ Yang Masih Missing:

1. **RSA Private Key** - Untuk generate signature (SN)
2. **Signature Formula** - String yang di-sign sebelum di-hash
3. **Secret Key** - Key tambahan untuk HMAC/signature

---

## 🎯 Next Steps

### 1. **Capture Signature Generation**

Jalankan Frida script untuk capture signature:

```bash
cd d:\10. Python\Generator\FreeReels\js

# Hook signature generation
frida -U FreeReels -l capture_signature.js --no-pause
```

Kemudian di aplikasi:
- Buka menu Profile
- Browse beberapa halaman
- Lihat output untuk SHA256/RSA signature

### 2. **Extract RSA Key dari APK**

Dari HP root:

```bash
# Pull APK
adb pull /data/app/~~*/*/com.freereels.app-*/base.apk

# Decompile
jadx -d decompiled base.apk

# Cari RSA key
cd decompiled
grep -r "MIIE\|MIIC\|MIID" . | grep -v ".jpg\|.png"

# Atau cari di assets
find . -name "*.pem" -o -name "*.key" -o -name "*.der"
```

### 3. **Analisis Signing Code**

Cari class yang berhubungan dengan signature di JADX:

```
Search text: "sign\|signature\|SN\|X-Sign\|X-SN"
Search text: "MessageDigest\|SHA256\|Base64"
```

Kemungkinan class:
- `com.freereels.app.security.*`
- `com.dramawave.core.network.*`
- `com.dramawave.shared.utils.*`

---

## 📝 Signature Generator (Draft)

File: `freereels_sn_generator.py`

**Formula (perlu konfirmasi dari APK):**

```python
# Signing string
signing_string = f"timestamp={timestamp}{method}{endpoint}{body}{device_id}{android_id}{secret_key}"

# SHA256 hash
hash = SHA256(signing_string)

# RSA Sign (perlu private key)
signature = RSA_sign(hash, private_key)

# Base64 encode
SN = Base64(signature)
```

**Headers yang diperlukan:**

```http
X-Timestamp: {timestamp_ms}
X-SN: {signature}
X-Sign: {signature}  # atau X-Sign
X-Device-Id: {device_id}
X-Android-Id: {android_id}
```

---

## 🛠️ Tools yang Tersedia

| File | Fungsi |
|------|--------|
| `freereels_sn_generator.py` | SN generator (placeholder, perlu RSA key) |
| `freereels_public_client.py` | Public API client (tanpa auth) |
| `js/capture_signature.js` | Frida hook untuk capture signature |
| `js/simple_capture.js` | Simple auth header capture |
| `js/frida_hook.js` | Full HTTP interceptor |

---

## 🔍 Reverse Engineering Checklist

- [ ] Extract APK dari device
- [ ] Decompile dengan jadx
- [ ] Cari RSA private key
- [ ] Cari signature generation code
- [ ] Hook signature dengan Frida
- [ ] Extract secret key
- [ ] Test signature generator
- [ ] Update Python client dengan signature

---

## 📚 Resources

### DramaBox Reference
- File: `dramabox_sn_generator.py`
- Menggunakan RSA SHA256withRSA
- Key parts di-obfuscate

### Frida Scripts
- `capture_signature.js` - Hook SHA256, Base64, RSA sign
- `simple_capture.js` - Capture auth headers
- `frida_hook.js` - Full HTTP interceptor

### Python Clients
- `freereels_sn_generator.py` - Client dengan signature (WIP)
- `freereels_public_client.py` - Public client (no auth)

---

## ⚠️ Notes Penting

1. **Signature adalah kunci** - Tanpa signature yang benar, semua request return 404
2. **RSA Key wajib** - Perlu di-extract dari APK
3. **Device-specific** - Beberapa endpoint mungkin butuh device ID yang valid
4. **App version matters** - Headers harus match dengan versi APK

---

## 🎓 Alternative Approach

Jika reverse engineering terlalu sulit:

1. **Gunakan APK Modded** - Cari versi mod yang sudah bypass signature
2. **Automate dengan UI Testing** - Gunakan Appium untuk automate aplikasi asli
3. **Screen Scraping** - Parse UI elements langsung dari app (perlu root)

---

**Last Updated:** 2026-02-23  
**Status:** Need RSA Key Extraction  
**Priority:** Hook signature generation dengan Frida
