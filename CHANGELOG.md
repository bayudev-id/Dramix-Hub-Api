# Changelog - Dramix Gateway & APIs

Semua perubahan pada **Dramix Hub API (Gateway)** dicatat dalam dokumen ini mengikuti standar [Keep a Changelog](https://keepachangelog.com/id/1.0.0/).

---

## [Unreleased]

### Changed
- **Internal Microservices Port Reallocation (6101-6107)**:
  - Migrasi seluruh port microservice internal dari range `7401-7407` ke range bebas konflik `6101-6107`:
    - `CineFlow Hub`: 7401 -> 6101
    - `WeTV API`: 7402 -> 6102
    - `KissKH API`: 7403 -> 6103
    - `MovieBox API`: 7404 -> 6104
    - `Viu API`: 7405 -> 6105
    - `FreeReels API`: 7406 -> 6106
    - `iQIYI API`: 7407 -> 6107
  - Menyelesaikan konflik `[Errno 98] Address already in use` di server / Mini PC akibat service legacy yang menempati port 7401-7406.
  - Memperbarui seluruh konfigurasi pada `ecosystem.config.js`, `deploy.sh` (UFW & health checks), launcher Windows (`start_all.bat`, `stop_all.bat`), default port di entrypoint masing-masing service, serta seluruh PocketBase hooks (`categories.pb.js`, `videos.pb.js`, `detail.pb.js`, `search.pb.js`, `source.pb.js`, `viu_proxy.pb.js`).
  - Memperbarui dokumentasi registry port di `PORTS.md`, `README.md`, dan panduan troubleshooting.

### Added
- **VIU HLS Manifest & AES-128 DRM Key Proxy (`pb_hooks/viu_proxy.pb.js`)**:
  - Proxy HLS playlist (`/api/modelles/viu/vuclip_vod.m3u8` dan `/api/modelles/viu/vuclip_airplay.m3u8`) melalui PocketBase port 8090.
  - Proxy AES-128 DRM key endpoint (`/api/modelles/viu/getkey`) dengan autentikasi internal API key terinjeksi di sisi gateway.
  - Menulis ulang URI tag `#EXT-X-KEY` dalam playlist `.m3u8` secara dinamis ke host gateway client port 8090.
- **Production 1-Click Deployment Script (`deploy.sh`)**:
  - Skrip deploy otomatis untuk Mini PC di `/opt/dramix_gateway` dikelola oleh PM2.
  - Otomatis deteksi arsitektur CPU dan unduh binary Linux PocketBase v0.40.4 jika belum ada.
  - Konfigurasi isolasi firewall UFW (allow port 8090, block port 7401-7407 dari akses eksternal/LAN).

### Security
- **Strict Microservice Loopback Binding (127.0.0.1)**:
  - Mengembalikan binding default service VIU (`services/viu_api/main.py`) ke `127.0.0.1`.
  - Mengonfigurasi `ecosystem.config.js` agar seluruh microservice internal (`cineflow:7401`, `wetv:7402`, `kisskh:7403`, `moviebox:7404`, `viu:7405`, `freereels:7406`, `iqiyi:7407`) terisolasi di `HOST: 127.0.0.1`, dan hanya PocketBase Gateway yang membuka port `0.0.0.0:8090` ke LAN.

### Fixed
- **VIU Playback Failure on Android ExoPlayer**:
  - Memperbaiki kegagalan pemutaran video VIU akibat stream URL sebelumnya mengarah langsung ke port 7405 yang tidak terbuka di LAN dan tidak memiliki otorisasi API key.
  - Rewrite stream URLs pada `/api/modelles/source` (`pocketbase/pb_hooks/source.pb.js`) agar seluruh manifest dan key diakses via PocketBase port 8090.

### Added
- **Provider Priority Ordering di `/api/modelles/models`**: Menetapkan urutan prioritas resmi provider pada endpoint models dengan priority map di `pocketbase/pb_hooks/models.pb.js`:
  - Posisi 1-7: WeTV, MovieBox, VIU, KissKH, iQIYI, Youku, FreeReels
  - Provider sisanya diurutkan alfabetis
  - Memastikan konsistensi urutan di seluruh aplikasi (Home, Search, Player).
- **Search Pagination Support (`has_more`)**: Menambahkan field `has_more` ke response `/api/modelles/search` dengan strategi per-provider:
  - **WeTV**: Calculate dari `total_results` (page * 10 < total)
  - **MovieBox**: Consume `pager.has_more` dari upstream
  - **iQIYI**: Consume `data.has_more` dari upstream
  - **FreeReels**: Consume `data.page_info.has_more` dari upstream
  - **VIU**: Heuristic `items.length > 0` (upstream tidak expose pagination)
  - **KissKH**: Default `false` (return full array 1 halaman)
  - **CineTv**: Default `false` (category search tanpa pagination)
  - **CineFlow Hub**: Consume `data.has_more` jika ada, else `false`

### Fixed
- **Search Portrait Cover Availability**: Audit endpoint `/api/modelles/search` untuk 24 provider. Hasil:
  - ✓ 15/24 provider (62.5%) menyediakan cover portrait lengkap: WeTV, MovieBox, VIU, KissKH, iQIYI, Youku, FreeReels, Anichin, Anichin V2, Animelovers, Bstation, CineMovies, CineTv, Mobinime, Samehadaku.
  - ✗ 9/24 provider sementara skip karena error upstream (CineFlow crash: 6 provider), inactive (1 provider), atau no-match results (2 provider).
  - Semua 15 provider sukses dikonfirmasi memiliki field `cover` atau fallback (`cover_portrait`, `vertical_cover`, `thumbnail`, `banner`, `poster`) dengan data non-empty.
- **Portrait Priority in Search Endpoint**: Update fallback order untuk WeTV (`cover_v` first) dan VIU (`cover_portrait` first) untuk prioritas portrait cover terhadap landscape fallback. CineFlow, iQIYI, FreeReels, KissKH, MovieBox sudah portrait-optimized di upstream.

---

## [1.2.0] - 2026-10-09

### Fixed
- **MovieBox Pagination Loop & Non-Trending Cutoff**: Memperbaiki penanganan kategori MovieBox pada `pocketbase/pb_hooks/videos.pb.js`. Untuk kategori kurasi statis (selain Rekomendasi/Trending), permintaan `pageNum > 1` kini langsung diputus dengan `has_more = false` dan array item kosong tanpa meneruskan request duplikat ke upstream microservice `:7404`. Field `has_more` hanya aktif jika kategori merupakan seksi Rekomendasi dan upstream mengembalikan boolean `pager.has_more: true` secara eksplisit.
- **Normalisasi Pagination Seluruh Provider (Gateway-Wide)**: Mengaudit dan menyempurnakan kalkulasi `has_more` pada `videos.pb.js` untuk seluruh 7 pipeline backend:
  - **KissKH**: Menghitung `hasMore = (pageNum * pageSize) < totalCount` dari metadata upstream. Memutus payload kosong jika page melampaui batas total item.
  - **Viu**: Menandai `has_more: false` jika item yang dikembalikan kurang dari ukuran halaman standar (20 item) atau kosong.
  - **FreeReels**: Mengonsumsi `has_more` dari root response atau `data.page_info.has_more`.
  - **iQIYI**: Menonaktifkan pagination pada kategori feed/home (`hasMore = false`), dan mengonsumsi `data.has_more` pada endpoint pencarian/katalog.
  - **CineFlow Upstream**: Mengonsumsi boolean eksplisit `cfRes.json.data.has_more` untuk ~17 provider (NetShort, Melolo, ShortMax, dll).

### Added
- **Panduan Pembelajaran & Pemecahan Masalah**: Penambahan [`docs/TROUBLESHOOTING_AND_LEARNING_GUIDE.md`](docs/TROUBLESHOOTING_AND_LEARNING_GUIDE.md) yang mengulas analisis akar masalah, normalisasi API 24 provider, hardware license binding, dan determinisme JSON.
- **Git Security & Clean Hygiene**: Menambahkan `.gitignore` root komprehensif untuk mencegah commit binary `pocketbase.exe`, database runtime `pb_data/`, dependensi `node_modules/`, cache Python `__pycache__/`, dan berkas rahasia `.env`.

### Changed
- Pembaruan dokumentasi port registry dan endpoint contract pada `PORTS.md`.

---

## [1.1.0] - 2026-10-08

### Added
- **Sistem Lisensi VIP Freemium**:
  - Migrasi skema database `licenses` pada `pocketbase/pb_migrations/1791503856_created_licenses.js`.
  - Hook endpoint aktivasi dan status lisensi pada `pocketbase/pb_hooks/license.pb.js` (`/api/license/activate`, `/api/license/status`).
  - Admin management tool berbasis PowerShell: `license-admin.ps1`.
- **Ekspansi Microservices Provider**:
  - Penambahan **FreeReels API** (port `7406`) pada `services/freereels_api/`.
  - Penambahan **iQIYI API** (port `7407`) pada `services/iqiyi_api/`.
  - Integrasi ke `ecosystem.config.js`, `start_all.bat`, dan `stop_all.bat`.
- **Metadata Tier Akses Episode Detail**:
  - Normalisasi status episode pada `detail.pb.js`: `is_vip`, `is_express`, `is_trailer`, `label`, dan `tags` (mendukung episode sewa, VIP, dan trailer).

---

## [1.0.0] - 2026-10-01

### Added
- Rilis perdana Dramix Gateway berbasis PocketBase (port `8090`).
- Orkestrasi microservice terpadu untuk CineFlow Hub (`7401`), WeTV (`7402`), KissKH (`7403`), MovieBox (`7404`), dan Viu (`7405`).
- 6 Endpoint API Terpadu:
  - `GET /api/modelles/models`
  - `GET /api/modelles/categories`
  - `GET /api/modelles/videos`
  - `GET /api/modelles/detail`
  - `GET /api/modelles/source`
  - `GET & POST /api/modelles/search`
- Skrip peluncur otomatis: `start_all.bat` dan `stop_all.bat`.
