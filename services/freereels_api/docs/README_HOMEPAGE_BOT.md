# 🎬 FreeReels Homepage Bot

Bot interaktif untuk browsing dan streaming drama dari FreeReels API.

## 📋 Fitur

- ✅ **Browse Homepage** - Lihat drama dari berbagai tab (Recommended, Trending, New Releases)
- ✅ **Detail Drama** - Lihat informasi lengkap drama (sinopsis, genre, tags, followers)
- ✅ **Daftar Episode** - Pilih episode yang ingin ditonton
- ✅ **Play Video** - Stream video dengan VLC atau browser
- ✅ **Multi-Subtitle** - Download/view subtitle dalam 13+ bahasa (termasuk Indonesia)
- ✅ **Pagination** - Support next page / load more untuk infinite scrolling

## 🚀 Cara Menggunakan

### Metode 1: Interactive Menu (Recommended)

```bash
python freereels_homepage_bot.py
```

**Flow:**
1. **Homepage** → Pilih tab (Recommended/Trending/New Releases)
2. **Pilih Drama** → Dari list yang ditampilkan
3. **Detail View** → Lihat info drama
4. **Episode List** → Pilih episode
5. **Play** → Stream dengan VLC atau browser

### Metode 2: Test Script (Non-Interactive)

```bash
python test_bot_full.py
```

Output akan menampilkan 10 drama pertama dan menyimpan list lengkap ke `test_dramas_list.json`.

## 📁 File Structure

```
FreeReels/
├── freereels_homepage_bot.py    # Bot utama (interactive)
├── test_bot_full.py             # Test script (non-interactive)
├── test_homepage_working.py     # Test API langsung
├── test_signature_formats.py    # Test berbagai format signature
├── docs/
│   └── KESIMPULAN_AKHIR.md      # Dokumentasi API lengkap
└── README_HOMEPAGE_BOT.md       # File ini
```

## 🔧 Configuration

Bot menggunakan credentials hardcoded dari Frida capture:

- **User ID**: `26326148095`
- **Auth Token**: `IsSG5rKFz7kfafVlqS8Ubq0JgT4N0a69`
- **Signature**: `edc1ec44568756ef6a23526dfbd089b1` (static dari capture)
- **Device ID**: `775eddf9b8392d6b`

Credentials ini ada di dalam `freereels_homepage_bot.py`.

## 📡 API Endpoint

**Base URL**: `https://apiv2.free-reels.com`

**Endpoint**: `/frv2-api/homepage/v2/tab/index`

**Parameters**:
- `tab_key`: Identifier tab (505=Recommended, 503=Trending, 516=New Releases)
- `position_index`: Pagination offset (default: 10000)
- `rec_trigger`: Recommendation trigger (default: 1)

## 🎥 Video Stream Format

Video tersedia dalam format **HLS (.m3u8)** dengan kualitas:
- 1080x1920 (Full HD)
- 720x1280 (HD)
- 540x960 (SD)
- 480x854
- 360x640

**Codec**:
- H.264 (compatible dengan semua player)
- H.265 (high efficiency, kualitas lebih baik)

## 📝 Subtitle Languages

Tersedia dalam 13+ bahasa:
- 🇮🇩 Indonesian (id-ID)
- 🇬🇧 English (en-US)
- 🇪🇸 Spanish (es-MX)
- 🇵🇹 Portuguese (pt-PT)
- 🇷🇺 Russian (ru-RU)
- 🇩🇪 German (de-DE)
- 🇫🇷 French (fr-FR)
- 🇮🇹 Italian (it-IT)
- 🇹🇷 Turkish (tr-TR)
- 🇯🇵 Japanese (ja-JP)
- 🇰🇷 Korean (ko-KR)
- 🇹🇭 Thai (th-TH)
- 🇻🇳 Vietnamese (vi-VN)
- Dan lainnya...

## 💡 Tips

1. **VLC Player**: Install VLC untuk pengalaman streaming terbaik
   - Download: https://www.videolan.org/vlc/

2. **Download Subtitle**: Gunakan menu "Download Subtitle" untuk menyimpan file .srt

3. **Tab Keys**: Beberapa tab_key yang bisa dicoba:
   - `505` - Recommended
   - `503` - Trending
   - `516` - New Releases
   - `622` - (custom, perlu dicoba)

## ⚠️ Troubleshooting

### Error: "Authentication failed or unauthorized"

Signature mungkin sudah expired. Update signature di `freereels_homepage_bot.py`:

```python
SIGNATURE = "edc1ec44568756ef6a23526dfbd089b1"  # Ganti dengan yang baru
SIGN = "fkb7tCW63BTpzQcd9+UIY0oL/ZM="
```

Untuk mendapatkan signature baru, gunakan Frida hooking (lihat `docs/KESIMPULAN_AKHIR.md`).

### Error: "VLC tidak ditemukan"

Bot akan otomatis membuka video di browser jika VLC tidak terinstall.

### Error: Unicode/Encoding di Windows

Sudah di-handle otomatis dengan UTF-8 encoding. Jika masih error, jalankan dengan:

```bash
chcp 65001
python freereels_homepage_bot.py
```

## 📚 Referensi

- `docs/KESIMPULAN_AKHIR.md` - Dokumentasi lengkap API dan Frida hooking
- `freereels_complete_client.py` - Client lengkap dengan semua headers
- `freereels_authenticated.py` - Client dengan authentication

## 🛠️ Development

Untuk development atau testing:

1. **Test API langsung**:
   ```bash
   python test_homepage_working.py
   ```

2. **Test signature formats**:
   ```bash
   python test_signature_formats.py
   ```

3. **Test full bot functions**:
   ```bash
   python test_bot_full.py
   ```

## 📄 License

Untuk keperluan edukasi dan testing saja.

---

**Created**: 2026-02-23  
**Based on**: KESIMPULAN_AKHIR.md  
**Status**: ✅ Working
