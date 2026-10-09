# FreeReels API Endpoint Discovery

Panduan untuk mencari dan intercept endpoint API dari aplikasi FreeReels/DramaWave.

## 📋 Prerequisites

### 1. Install Frida
```bash
pip install frida-tools
```

### 2. Setup Frida Server di Android
1. Download `frida-server` yang sesuai dengan arsitektur device:
   - https://github.com/frida/frida/releases
   - Pilih: `frida-server-{version}-android-{arch}.xz`
   
2. Extract dan push ke Android:
```bash
adb push frida-server /data/local/tmp/frida-server
adb shell chmod 755 /data/local/tmp/frida-server
```

3. Jalankan Frida Server:
```bash
adb shell
su
/data/local/tmp/frida-server &
```

### 4. Verify Connection
```bash
frida-ps -U
```

---

## 🚀 Cara Menggunakan

### 📌 Windows Users (Recommended)

**Gunakan PowerShell Script (Auto-replace log):**

```powershell
# Buka PowerShell di folder FreeReels
cd d:\10. Python\Generator\FreeReels

# Jalankan dengan log otomatis
.\run_frida.ps1

# Atau dengan SSL Bypass
.\run_frida.ps1 -UseSslBypass

# Jalankan tanpa save log
.\run_frida.ps1 -NoLog

# Target package lain
.\run_frida.ps1 -PackageName com.dramawave.app
```

**Atau gunakan Batch Script:**
```cmd
cd d:\10. Python\Generator\FreeReels
run_frida.bat
```

> 📝 **Note:** Script PowerShell/Batch akan otomatis **menghapus log lama** dan membuat log baru setiap kali dijalankan.

---

### 📌 Manual Command (All Platforms)

### Opsi 1: Hook HTTP Requests (frida_hook.js)

Script ini akan intercept semua HTTP/HTTPS request yang dilakukan aplikasi.

```bash
# Jalankan script hook
frida -U -f com.freereels.app -l frida_hook.js --no-pause
```

**Atau** jika aplikasi sudah terinstall:

```bash
# Attach ke aplikasi yang sedang berjalan
frida -U com.freereels.app -l frida_hook.js
```

### Opsi 2: Bypass SSL Pinning (ssl_bypass.js)

Gunakan script ini jika aplikasi memiliki SSL Pinning yang ketat.

```bash
# Bypass SSL pinning + monitor traffic
frida -U -f com.freereels.app -l ssl_bypass.js --no-pause
```

### Opsi 3: Kombinasi (Recommended)

Gabungkan kedua script untuk hasil maksimal:

```bash
# Buat script kombinasi
cat ssl_bypass.js frida_hook.js > combined.js

# Jalankan
frida -U -f com.freereels.app -l combined.js --no-pause
```

### Opsi 4: Save Output ke Log File

```bash
# Linux/Mac
frida -U -f com.freereels.app -l frida_hook.js --no-pause | tee frida_output.log

# Windows PowerShell
frida -U -f com.freereels.app -l frida_hook.js --no-pause 2>&1 | Out-File frida_output.log

# Windows CMD
frida -U -f com.freereels.app -l frida_hook.js --no-pause > frida_output.log 2>&1
```

---

## 📺 Output yang Diharapkan

Setelah script berjalan, Anda akan melihat output seperti:

```
========================================
[*] Starting HTTP interception for FreeReels/DramaWave...
========================================

[+] OkHttpClient.newCall hooked
[+] OkHttpClient.execute hooked
[+] Retrofit.create hooked
...

[OKHTTP] GET
URL: https://api.mydramawave.com/v1/theater/feed?tab=recommend
Headers: Authorization: Bearer xxx...
========================================

[RETROFIT BASE URL] https://api.mydramawave.com/
```

---

## 🔍 Endpoint Penting yang Dicari

Berdasarkan analisis smali, berikut endpoint yang kemungkinan ada:

### Theater/Feed Endpoints
- `/theater/feed` - Main feed content
- `/theater/recommend` - Recommended content
- `/theater/hot_list` - Popular content

### Video/Content Endpoints
- `/video/detail` - Video detail information
- `/video/unlock` - Unlock episode
- `/video/next` - Next episode suggestion

### User/Wallet Endpoints
- `/user/wallet` - User balance
- `/user/vip` - VIP subscription
- `/purchase/store` - Purchase history

### Novel Endpoints
- `/novel/list` - Novel catalog
- `/novel/chapter` - Chapter content
- `/novel/unlock` - Unlock chapter

---

## 🛠️ Troubleshooting

### Problem: "Failed to spawn: unable to find process"
**Solution:**
```bash
# Pastikan frida server berjalan
adb shell ps | grep frida

# Restart frida server
adb shell "su -c '/data/local/tmp/frida-server &'"
```

### Problem: "SSLHandshakeException" masih muncul
**Solution:**
1. Gunakan `ssl_bypass.js` terlebih dahulu
2. Pastikan frida server versi terbaru
3. Coba restart aplikasi

### Problem: Script tidak menampilkan output
**Solution:**
1. Pastikan package name benar: `com.freereels.app`
2. Cek dengan `frida-ps -U` untuk melihat package name yang tepat
3. Interact dengan aplikasi (scroll, tap) untuk trigger request

---

## 📁 File Structure

```
FreeReels/
├── freereels_client.py      # 🎬 Interactive Drama Browser & Player (NEW!)
├── requirements.txt         # Python dependencies
├── README.md                # Dokumentasi utama
├── CLIENT_README.md         # 📖 Panduan Interactive Client (NEW!)
├── API_ENDPOINTS.md         # Daftar API endpoints
├── JADX_ANALYSIS.md        # Hasil analisis decompiled APK
├── frida_output.log         # Output log (auto-replaced setiap run)
├── search_endpoint.py       # Python script untuk search di hasil decompile
├── run_frida.bat            # Windows batch runner (auto-clear log)
├── run_frida.ps1            # PowerShell runner (auto-clear log)
│
├── js/                      # Frida scripts
│   ├── frida_hook.js        # HTTP request interceptor (10 hooks)
│   └── ssl_bypass.js        # SSL pinning bypass (14 techniques)
│
└── docs/                    # Additional documentation
```

**Log File:**
- `frida_output.log` akan **dihapus dan dibuat baru** setiap kali menjalankan `run_frida.bat` atau `run_frida.ps1`
- Log berisi semua HTTP request yang di-intercept
- Format: URL, Method, Headers, Body

**Interactive Client:**
- `freereels_client.py` - Script Python dengan menu interaktif untuk browsing drama
- Jalankan: `python freereels_client.py`
- Lihat `CLIENT_README.md` untuk panduan lengkap

**Frida Scripts:**
- Lokasi: `js/frida_hook.js` dan `js/ssl_bypass.js`
- Gunakan dengan: `frida -U -f com.freereels.app -l js/frida_hook.js --no-pause`

---

## 🔬 Analisis Static (Decompiled APK)

### 📍 NetworkDiagnosisViewModel Discovery

File penting yang ditemukan di JADX:
```
com/dramawave/feature/profile/diagnosis/viewmodel/NetworkDiagnosisViewModel.kt
```

Class ini berisi **hardcoded test endpoints** untuk network diagnosis. Dari sini kita bisa menemukan:

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

**Test Video URLs:**
```
https://video-v1.mydramawave.com/vt/d2c30405-4f42-4d68-9c33-9ba408c57816/
  ├── h264-ecf3ad0b-73bb-4392-9f02-d8c0b6dcdda2.m3u8
  └── h265-ecf3ad0b-73bb-4392-9f02-d8c0b6dcdda2.m3u8
```

### 🔐 Authentication Requirements

API FreeReels memerlukan authentication untuk sebagian besar endpoint:

**Required Headers:**
```
Authorization: Bearer {jwt_token}
X-Device-Id: {unique_device_id}
X-App-Version: 2.1.91
X-Platform: android
User-Agent: FreeReels/2.1.91 (Android 13; SM-G998B)
```

**Cara Mendapatkan Token:**
1. **Frida Hook** (Recommended) - Auto capture dari aplikasi
2. **Burp Suite** - Manual intercept
3. **HTTP Canary** - No root required
4. **ADB Logcat** - Root required

📖 **Lihat**: `../HOW_TO_GET_TOKEN.md` untuk panduan lengkap

Lokasi di decompiled APK:
```
smali/com/dramawave/service/api/repository/
```

Found repository files:
- `TheaterRepository.smali` - Theater/feed content
- `VideoRepository.smali` - Video operations
- `UserRepository.smali` - User operations
- `NovelRepository.smali` - Novel content
- `PurchaseRepository.smali` - Purchase/wallet
- `q1.smali`, `C2800q1.smali` - Profile repository
- `R2.smali`, `X2.smali` - Additional repositories
- `A0.smali` - `R0.smali` (numbered repositories)
- `novel/a.smali` - `novel/x.smali` (Novel-specific APIs)

### 📄 Documentation Files

- **`JADX_ANALYSIS.md`** - Detailed analysis dari decompiled APK
- **`API_ENDPOINTS.md`** - Complete list of API endpoints
- **`frida_output.log`** - Log dari frida hooks (auto-replaced setiap run)

---

## 💡 Tips

1. **Filter Output**: Gunakan `grep` untuk filter URL tertentu
   ```bash
   frida -U -f com.freereels.app -l frida_hook.js --no-pause | grep -E "api|video|theater"
   ```

2. **Save Output**: Simpan output ke file untuk analisis
   ```bash
   frida -U -f com.freereels.app -l frida_hook.js --no-pause > output.log
   ```

3. **Combine with Burp**: Setup Burp Suite sebagai proxy
   ```bash
   # Setup proxy di Android
   adb shell settings put global http_proxy <your-ip>:8888
   ```

4. **Monitor Specific Class**: Hook class tertentu
   ```javascript
   // Tambahkan ke frida_hook.js
   var TheaterRepo = Java.use("com.dramawave.service.api.repository.TheaterRepository");
   TheaterRepo.getFeedData.implementation = function() {
       console.log("[TheaterRepo] getFeedData called");
       return this.getFeedData();
   };
   ```

---

## 📚 Resources

- Frida Documentation: https://frida.re/docs/
- jadx (Decompiler): https://github.com/skylot/jadx
- Apktool: https://apktool.org/
- Burp Suite: https://portswigger.net/burp

---

**Last Updated**: 2026-02-23
**Target App**: FreeReels v2.1.91 (200191001)
