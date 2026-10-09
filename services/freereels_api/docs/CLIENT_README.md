# 🎬 FreeReels Client - Interactive Drama Browser & Player

Python client untuk browsing dan watch drama dari FreeReels/DramaWave dengan menu interaktif.

---

## ✨ Features

- ✅ **Browse Drama** - Theater feed, hot list, coming soon
- ✅ **Search** - Cari drama by keyword
- ✅ **Drama Detail** - Informasi lengkap drama (synopsis, cast, rating, episodes)
- ✅ **Episode List** - List semua episodes dengan status free/locked
- ✅ **Video Playback** - Play episode dengan external player (browser/VLC/MPC)
- ✅ **Subtitles** - View dan download subtitles
- ✅ **Comments** - Baca comments dari users
- ✅ **MyList** - Save drama ke watchlist (perlu login)
- ✅ **User Profile** - View profile, coins, VIP status
- ✅ **Daily Rewards** - Check-in daily untuk dapat coins
- ✅ **Authentication** - Login dengan phone OTP

---

## 📦 Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Atau manual:

```bash
pip install requests pyperclip
```

### 2. Run Application

```bash
python freereels_client.py
```

---

## 🎯 Usage Flow

```
MAIN MENU
├── 📺 Theater Feed
│   └── Pilih tab (recommend/picks_for_you/hybrid)
│       └── Pilih drama dari list
│           └── DRAMA DETAIL
│               ├── 📋 View Episodes
│               │   └── Pilih episode
│               │       └── EPISODE DETAIL
│               │           ├── ▶️ PLAY (pilih player)
│               │           ├── 📥 Get Video URL
│               │           └── 📊 Get Subtitles
│               ├── ▶️ Play First Episode
│               ├── 💬 View Comments
│               └── ❤️ Add to MyList
├── 🔥 Hot/Trending
├── 📅 Coming Soon
├── 🔍 Search
├── 🎭 Popular Actors
├── 📋 My Watchlist (perlu login)
├── 👤 User Profile
│   └── 🔐 Login (phone + OTP)
└── 🎁 Daily Rewards
    ├── 📅 Daily Check-in
    └── 📋 View Daily Tasks
```

---

## 📸 Screenshots

### Main Menu
```
============================================================
  FREEREELS - DRAMA BROWSER
============================================================

  Pilih menu:

  [1] 📺 Theater Feed (Recommend)
  [2] 🔥 Hot/Trending Drama
  [3] 📅 Coming Soon
  [4] 🔍 Search Drama
  [5] 🎭 Popular Actors
  [6] 📋 My Watchlist
  [7] 👤 User Profile
  [8] 🎁 Daily Rewards
  [0] Back/Exit
```

### Drama Detail
```
============================================================
  📺 DRAMA DETAIL
============================================================

  ==================================================
  📺 Love Between Fairy and Devil

  📝 Series ID: S12345
  🎬 Type: Drama
  📊 Rating: 9.2
  📀 Total Episodes: 36
  📅 Status: Ongoing
  🌟 Cast: Yu Shuxin, Wang Hedi

  📖 Synopsis:
      A love story between a fairy and a devil...
      (full synopsis displayed here)

  🏷️  Genres: Romance, Fantasy, Comedy

  🖼️  Thumbnail: https://...
  ==================================================

  [1] 📋 View Episodes
  [2] ▶️ Play First Episode
  [3] 💬 View Comments
  [4] ❤️ Add to MyList
  [5] 🔍 Search Similar
  [0] Back
```

### Episode Playback
```
============================================================
  ▶️ PLAYING EPISODE
============================================================

[*] Getting video URL...

  🎬 Video URL: https://video-v1.mydramawave.com/vt/.../episode1.m3u8

  Choose player:
  [1] Open in Browser
  [2] Open with VLC
  [3] Open with MPC-HC
  [4] Copy URL to clipboard
  [0] Back
```

---

## 🔧 Configuration

Edit `freereels_client.py` untuk customize:

```python
# Base URLs (dari JADX analysis)
BASE_URL = "https://api.mydramawave.com"
VIDEO_BASE_URL = "https://video-v1.mydramawave.com"

# Headers
DEFAULT_HEADERS = {
    "User-Agent": "FreeReels/2.1.91 (Android 13)",
    "Content-Type": "application/json",
}
```

---

## 🎮 Keyboard Controls

- **Angka 0-9** - Pilih menu
- **Enter** - Confirm
- **y/n** - Yes/No confirmation

---

## 📋 API Endpoints Used

| Feature | Endpoint |
|---------|----------|
| Theater Feed | `GET /v1/theater/feed` |
| Hot List | `GET /v1/theater/hot_list` |
| Drama Detail | `GET /v1/video/detail` |
| Search | `GET /v1/search/query` |
| Comments | `GET /v1/comment/list` |
| MyList | `GET/POST/DELETE /v1/mylist` |
| Login | `POST /v1/user/login` |
| Profile | `GET /v1/user/profile` |
| Daily Check-in | `POST /v1/reward/checkin` |

---

## 🔐 Authentication

Beberapa fitur memerlukan login:
- My Watchlist
- Daily Rewards
- Add Comments
- Unlock Episodes

**Login flow:**
1. Pilih menu "👤 User Profile"
2. Pilih "Login"
3. Masukkan phone number (format: 628...)
4. Masukkan OTP code (dari SMS)
5. Token akan disimpan di session

---

## ⚠️ Limitations

1. **Video Playback**: Script tidak play video langsung, tapi membuka URL di external player
2. **Locked Episodes**: Perlu coins/VIP untuk unlock (simulated saja di script)
3. **Rate Limiting**: API mungkin ada rate limit
4. **Region Lock**: Beberapa content mungkin region-specific

---

## 🛠️ Troubleshooting

### "Missing package: requests"
```bash
pip install requests pyperclip
```

### "Failed to get data"
- Check internet connection
- API endpoint mungkin berubah
- Perlu authentication untuk beberapa endpoint

### "Video URL tidak bisa di-play"
- URL mungkin expired
- Perlu authentication token
- Region lock

### "VLC/MPC-HC not found"
- Install VLC: https://www.videolan.org/
- Install MPC-HC: https://github.com/clsid2/mpc-hc
- Atau gunakan "Open in Browser"

---

## 📁 Project Structure

```
FreeReels/
├── freereels_client.py    # Main interactive client
├── requirements.txt        # Python dependencies
├── CLIENT_README.md       # This file
├── frida_hook.js          # Frida HTTP interceptor
├── ssl_bypass.js          # SSL pinning bypass
├── API_ENDPOINTS.md       # API documentation
├── JADX_ANALYSIS.md      # Decompiled APK analysis
└── README.md              # Main documentation
```

---

## 🚀 Advanced Usage

### Custom Base URL

```python
client = FreeReelsClient(base_url="https://apiv2.free-reels.com")
```

### Manual API Calls

```python
from freereels_client import FreeReelsClient

client = FreeReelsClient()

# Get theater feed
feed = client.get_theater_feed(tab="recommend", page=1)

# Search drama
results = client.search(query="romance", page=1)

# Get drama detail
detail = client.get_video_detail(series_id="S12345")
```

### Set Auth Token

```python
client.set_auth(token="your_jwt_token", user_id="12345")
```

---

## 📝 To-Do

- [ ] Download episode untuk offline viewing
- [ ] Auto-next episode
- [ ] Remember last watched episode
- [ ] Export watchlist to file
- [ ] Screenshot feature
- [ ] Share drama to social media

---

## 📚 Resources

- **Main Documentation**: `README.md`
- **API Endpoints**: `API_ENDPOINTS.md`
- **JADX Analysis**: `JADX_ANALYSIS.md`
- **Frida Hooks**: `frida_hook.js`

---

## ⚖️ Disclaimer

Script ini untuk **educational purposes** saja. 

- Gunakan dengan bijak
- Jangan untuk commercial use
- Respect terms of service aplikasi
- Support official release dengan subscribe VIP

---

**Version**: 1.0.0  
**Last Updated**: 2026-02-23  
**Author**: Generated from JADX analysis
