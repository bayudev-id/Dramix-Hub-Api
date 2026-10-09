# 🔑 Cara Mendapatkan Bearer Token FreeReels

Panduan lengkap untuk mendapatkan authentication token (Bearer token) dari aplikasi FreeReels.

---

## ⚡ Quick Start

**Cara termudah:** Gunakan Frida untuk capture token secara otomatis!

```bash
# 1. Jalankan Frida hook
frida -U -f com.freereels.app -l js/frida_hook.js --no-pause

# 2. Buka aplikasi FreeReels di Android
# 3. Token akan ter-capture di frida_output.log

# 4. Di Python client, pilih:
#    [7] User Profile -> Load from Frida Log
```

---

## 📱 Metode 1: Frida Hook (RECOMMENDED)

### Langkah 1: Setup Frida Server

```bash
# Push frida-server ke Android
adb push frida-server /data/local/tmp/frida-server
adb shell chmod 755 /data/local/tmp/frida-server

# Jalankan frida server
adb shell /data/local/tmp/frida-server &
```

### Langkah 2: Jalankan Hook Script

```bash
cd d:\10. Python\Generator\FreeReels
frida -U -f com.freereels.app -l js/frida_hook.js --no-pause
```

### Langkah 3: Buka Aplikasi

1. Buka aplikasi FreeReels di Android
2. Login jika belum
3. Browse beberapa halaman untuk generate traffic

### Langkah 4: Cek Log

Token akan muncul di output seperti ini:

```
========================================
[OKHTTP] GET
URL: https://api.mydramawave.com/v1/user/profile
Headers: 
  Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
  Content-Type: application/json
========================================
```

**Copy token** setelah kata `Bearer ` (tanpa spasi).

### Langkah 5: Load Token ke Client

```bash
python freereels_client.py

# Pilih menu:
[7] User Profile
  -> [3] Load from Frida Log

# Token akan otomatis diambil dari frida_output.log!
```

---

## 🔍 Metode 2: Burp Suite

### Setup Burp Suite

1. **Install Burp Suite**: https://portswigger.net/burp/communitydownload
2. **Setup Proxy** di Android:
   - WiFi Settings → Proxy → Manual
   - Hostname: IP komputer Anda
   - Port: 8888
3. **Install CA Certificate**:
   - Buka http://burpsuite di browser Android
   - Download dan install certificate

### Capture Request

1. Buka Burp Suite → Proxy → Intercept → On
2. Buka aplikasi FreeReels
3. Lihat request di Burp
4. Cari header: `Authorization: Bearer xxx`

### Contoh Request di Burp

```http
GET /v1/theater/feed?tab=recommend HTTP/1.1
Host: api.mydramawave.com
User-Agent: FreeReels/2.1.91 (Android 13)
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
```

**Copy** nilai setelah `Bearer `.

---

## 📲 Metode 3: HTTP Canary (No Root)

### Install HTTP Canary

1. Download dari Play Store atau APKPure
2. Install dan buka aplikasi
3. Grant permission yang diminta

### Capture Traffic

1. Tekan tombol **Start** di HTTP Canary
2. Buka FreeReels
3. Browse beberapa halaman
4. Stop capture

### Cari Token

1. Cari request ke `api.mydramawave.com`
2. Buka detail request
3. Lihat di **Headers** → **Authorization**
4. Copy nilai setelah `Bearer `

---

## 🛠️ Metode 4: ADB Logcat (Root Required)

### Langkah 1: Enable Root Debugging

```bash
adb root
adb shell setprop debug.app.package com.freereels.app
```

### Langkah 2: Monitor Logcat

```bash
adb logcat | grep -i "authorization\|bearer\|token"
```

### Langkah 3: Buka Aplikasi

Buka FreeReels dan lihat output logcat untuk token.

---

## 💾 Metode 5: Extract dari Shared Preferences (Root Required)

### Lokasi File Token

```
/data/data/com.freereels.app/shared_prefs/
```

File yang mungkin berisi token:
- `user_prefs.xml`
- `auth_prefs.xml`
- `app_config.xml`

### Cara Extract

```bash
# Pull file dari Android
adb pull /data/data/com.freereels.app/shared_prefs/user_prefs.xml

# Buka dengan text editor
# Cari tag seperti: <string name="auth_token">xxx</string>
```

---

## 🔐 Decode JWT Token (Optional)

Token FreeReels menggunakan format JWT. Anda bisa decode untuk melihat isi:

### Online Decoder
- https://jwt.io/
- Paste token Anda
- Lihat payload (hati-hati, token adalah secret!)

### Python Decode

```python
import jwt

token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Decode tanpa verify (hanya untuk lihat isi)
decoded = jwt.decode(token, options={"verify_signature": False})
print(decoded)
```

### Isi Token Biasanya Berisi:
```json
{
  "user_id": "12345",
  "username": "user@example.com",
  "exp": 1234567890,
  "iat": 1234567800
}
```

---

## 📝 Format Token

Token FreeReels biasanya seperti ini:

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiMTIzNDUiLCJleHAiOjE3MDg2NzUyMDB9.abc123def456
```

Terdiri dari 3 part dipisahkan titik (`.`):
1. **Header** - Algorithm info
2. **Payload** - User data
3. **Signature** - Verification

---

## ⚠️ Troubleshooting

### Token Expired

**Symptom:** API return 401 Unauthorized

**Solution:**
- Token JWT ada expiry time (biasanya 7-30 hari)
- Login ulang atau capture token baru

### Token Invalid

**Symptom:** API return 401/403

**Possible causes:**
- Token tidak lengkap (terpotong)
- Ada spasi di awal/akhir
- Wrong token format

**Solution:**
- Pastikan copy seluruh token (bisa 200-500 karakter)
- Trim spasi: `token.strip()`
- Token harus mulai dengan `eyJ`

### Device ID Required

**Symptom:** API return 403 Forbidden

**Solution:**
Beberapa endpoint memerlukan `X-Device-Id` header.

Di Python client sudah auto-generate, atau bisa set manual:

```python
client.session.headers.update({
    "X-Device-Id": "your-device-id-here"
})
```

---

## 🎯 Tips

1. **Simpan Token**: Setelah dapat token, simpan di file aman
2. **Jangan Share**: Token = akses ke akun Anda!
3. **Auto-Load**: Gunakan fitur "Load from Frida Log" di client
4. **Multiple Accounts**: Bisa punya token untuk multiple accounts

---

## 📚 Related Files

- `freereels_client.py` - Python client
- `js/frida_hook.js` - Frida hook script
- `frida_output.log` - Auto-generated log
- `README.md` - Main documentation

---

**Last Updated**: 2026-02-23  
**Version**: 1.0.0
