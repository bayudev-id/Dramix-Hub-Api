# Changelog - Dramix Gateway & APIs

Semua perubahan pada **Dramix Hub API (Gateway)** dicatat dalam dokumen ini mengikuti standar [Keep a Changelog](https://keepachangelog.com/id/1.0.0/).

---

## [Unreleased]

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
