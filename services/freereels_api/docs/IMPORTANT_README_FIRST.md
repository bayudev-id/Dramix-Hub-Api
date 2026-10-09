# 🚨 PENTING: API FreeReels Memerlukan Authentication!

## ❌ Masalah

Semua API requests mengembalikan **404 Not Found** karena:

1. ✅ **Base URL benar**: `https://api.mydramawave.com`
2. ❌ **Authentication required**: Semua endpoint memerlukan Bearer token
3. ❌ **Headers tidak lengkap**: Device ID, platform headers diperlukan

## ✅ Solusi

### Anda HARUS melakukan salah satu dari ini:

---

## 🔥 METODE 1: Frida Hook (PALING MUDAH)

### Langkah 1: Setup Frida Server di Android

```bash
# Download frida-server dari https://github.com/frida/frida/releases
# Pilih yang sesuai dengan architecture Android Anda

# Push ke Android
adb push frida-server-android-16.x.x /data/local/tmp/frida-server
adb shell chmod 755 /data/local/tmp/frida-server

# Jalankan
adb shell /data/local/tmp/frida-server &
```

### Langkah 2: Jalankan Hook Script

```bash
cd d:\10. Python\Generator\FreeReels

# Jalankan frida hook
frida -U -f com.freereels.app -l js/frida_hook.js --no-pause
```

### Langkah 3: Buka Aplikasi FreeReels

1. Aplikasi akan otomatis terbuka
2. Login jika belum
3. Browse beberapa halaman (Home, Search, Drama detail)
4. Tutup aplikasi setelah beberapa detik

### Langkah 4: Cek Log

Token dan endpoint akan ter-capture di:
- **Output terminal** (langsung terlihat)
- **File**: `frida_output.log`

Anda akan melihat seperti ini:

```
========================================
[OKHTTP] GET
URL: https://api.mydramawave.com/v1/search/query?q=love&type=drama
Headers: 
  Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
========================================
```

### Langkah 5: Load Token ke Python Client

```bash
python freereels_client.py

# Pilih menu:
[7] User Profile
  -> [3] Load from Frida Log

# Token otomatis loaded!
```

---

## 📱 METODE 2: HTTP Canary (No Root)

### Download HTTP Canary

1. Play Store: "HTTP Canary"
2. Atau download APK dari: https://apkpure.com/http-canary

### Cara Pakai

1. Buka HTTP Canary
2. Tekan **Start** (ikon play)
3. Grant permission
4. Buka FreeReels
5. Browse beberapa halaman
6. Stop capture

### Cari Token

1. Cari request ke `api.mydramawave.com`
2. Buka detail request
3. Lihat tab **Request Headers**
4. Cari: `Authorization: Bearer xxx`
5. Copy token-nya

---

## 💻 METODE 3: Burp Suite

### Setup

1. Download Burp Suite: https://portswigger.net/burp/communitydownload
2. Install dan buka
3. Proxy → Intercept → On

### Configure Android Proxy

1. WiFi Settings → Proxy → Manual
2. Hostname: IP komputer Anda
3. Port: 8888
4. Install Burp CA certificate dari http://burpsuite

### Capture

1. Buka FreeReels
2. Lihat request di Burp
3. Copy Authorization header

---

## 🎯 Setelah Dapat Token

### Opsi 1: Input Manual

```bash
python freereels_client.py

[7] User Profile
  -> [2] Input Manual Token

# Paste token
```

### Opsi 2: Auto-Load dari Frida Log

```bash
python freereels_client.py

[7] User Profile
  -> [3] Load from Frida Log

# Pilih token dari list
```

---

## ⚠️ Troubleshooting

### "Frida tidak bisa connect"

```bash
# Cek frida server berjalan
adb shell ps | grep frida

# Restart frida server
adb shell "su -c 'killall frida-server'"
adb shell /data/local/tmp/frida-server &
```

### "Tidak ada token di log"

- Pastikan sudah **login** di aplikasi
- Browse beberapa halaman untuk generate traffic
- Cek frida_hook.js berjalan dengan benar

### "Token expired"

- Token JWT ada expiry time (7-30 hari)
- Capture ulang token baru

---

## 📚 Files Terkait

- `js/frida_hook.js` - Frida hook script
- `js/ssl_bypass.js` - SSL pinning bypass
- `freereels_client.py` - Python client
- `frida_output.log` - Auto-generated log
- `HOW_TO_GET_TOKEN.md` - Panduan lengkap

---

## 🎓 Next Steps

Setelah dapat token:

1. ✅ Load token ke Python client
2. ✅ Test search drama
3. ✅ Browse theater feed
4. ✅ Lihat detail drama
5. ✅ Play episode

---

**Tanpa token, API tidak bisa diakses!**
