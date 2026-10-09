# Changelog - Dramix Gateway & APIs

Semua perubahan pada **Dramix Hub API (Gateway)** dicatat dalam dokumen ini mengikuti standar [Keep a Changelog](https://keepachangelog.com/id/1.0.0/).

---

## [Unreleased]

### Added
- **Provider Priority Ordering di `/api/modelles/models`**: Menetapkan urutan prioritas resmi provider pada endpoint models dengan priority map di `pocketbase/pb_hooks/models.pb.js`:
  - Posisi 1-7: WeTV, MovieBox, VIU, KissKH, iQIYI, Youku, FreeReels
  - Provider sisanya diurutkan alfabetis
  - Memastikan konsistensi urutan di seluruh aplikasi (Home, Search, Player).

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
