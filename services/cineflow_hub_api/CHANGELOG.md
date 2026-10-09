# Changelog — CineFlow API Proxy

Semua perubahan penting pada project ini dicatat di sini.

Format berdasarkan [Keep a Changelog](https://keepachangelog.com/),
dan versi mengikuti [Semantic Versioning](https://semver.org/).

---

## [2.3.0] — 2026-09-01

### Fixed
- **Moviebox loading 90 detik** — Akar masalah: `/media` proxy pakai `httpx.AsyncClient.get()` yang buffer seluruh 1.29GB file ke memory sebelum kirim ke browser. Diganti `client.send(req, stream=True)` + `aiter_bytes()` — byte langsung diforward, browser dapat moov (byte 36) dalam ms, metadata loaded dalam 6s.
- **Moviebox DASH gagal** — Stream DASH (wrapper h5-api + direct sbcdn2) bermasalah di pipeline. Untuk moviebox, DASH difilter, hanya MP4 dipakai. Provider lain tetap DASH priority.
- **Stream ranking MP4 1080 menang atas DASH** — `parseInt("1080")` = 1080 > 1000 (DASH base). DASH bases dinaikkan ke 100000/50000 agar MP4 tak bisa menyalip.
- **QualityOptions default salah** — Dua stream DASH punya quality "Auto" — `find(q => q.default)` ambil yg pertama di urutan asli (wrapper, gagal). Sekarang qualityOptions dibangun dari `sortedStreams`, default = idx 0.
- **DASH manifest HEAD response** — `/media` HEAD balikin `application/octet-stream` (header asli CDN OSS). Shaka probe manifest lewat HEAD → tolak. Sekarang HEAD balikin `application/dash+xml` kalau target .mpd.
- **Duplicate hooks dihapus** — 7 file hooks duplikat (useProviders, useSections, useSectionContent, useDramaDetail, useEpisodesList, usePlaybackStream, useSearch) dihapus. Semua data fetching terpusat di `useDrama.ts`. Juga hapus dead code `handleSearchChange` di Home.tsx.

### Changed
- **Media proxy streaming** — `/media` endpoint sekarang pakai `client.send(req, stream=True)` + persistent client pool (`_get_media_client()`). HEAD pakai `client.head()`. Koneksi CDN reuse, tak bikin TCP+TLS handshake baru tiap request.
- **CDN pre-warm** — Sebelum player init, fetch Range 512KB ke default stream URL. CDN edge cache panas, cold start 87s hilang.
- **Subtitle size jadi angka px** — Label size subtitle ganti dari huruf (XS/SM/MD/LG/XL/XXL) ke nilai px (12px-32px). Tambah 3 ukuran besar baru: 36px, 40px, 44px.
- **Bump versi**: `2.2.0` → `2.3.0`

---

## [2.2.0] — 2026-08-31

### Fixed
- **HP logout tiap refresh token** — Root cause: `_write_to_phone_async()` dipanggil di setiap cabang `refresh_token_v2()`, yang menjalankan `force-stop com.cineflow.app` via ADB. HP app mati paksa → user buka lagi → HP rotate refresh token → proxy dapet 401 `refresh_token_rotated`.
  - Hapus semua panggilan `_write_to_phone_async()` dari 3 cabang: rotated recovery, expired/invalid extract, dan refresh sukses normal.
  - `_save_to_cache()` tetap jalan (simpan token lokal).
  - `_extract_from_phone()` tetap jalan (baca token dari HP via ADB, **tanpa** write-back).
  - Server dan HP sekarang **independen** — tidak saling force-stop atau overwrite token.

### Changed
- Bump versi: `2.0.0` → `2.2.0` (lompat karena 2.1.0 dipakai changelog terpisah).
- Log startup sekarang menampilkan versi aplikasi.

---

## [2.1.0] — 2026-08-29

### Fixed
- **Token auto-extract dari HP terus-menerus** — Setiap error refresh langsung asumsi "token di-rotate" dan extract dari HP. Sekarang hanya extract jika 401 + expired/invalid.
- **Cache warning muncul 2x** — `TokenManager()` di-init 2x di main.py (duplicate code). Hapus duplikat.
- **Token sync ke HP setiap refresh** — `_write_to_phone()` di-disable di refresh normal. Server dan HP independen.

### Changed
- `_load_from_cache()`: message lebih jelas, tampilkan email user.
- `refresh_token_v2()`: hanya extract dari HP jika error 401 + expired/invalid.
- Flow: Server bisa refresh token independen tanpa HP untuk operasi normal.

---

## [2.0.0] — 2026-08-?? (Estimasi)

### Changed
- Full rewrite proxy dengan v2 Auth Flow.
- Token Manager dengan refresh token rotation handling.
- Dashboard HTML premium.
- Dukungan endpoint `/api/modelles/*`, `/api/app/*`, `/api/token/*`.
- Auto-refresh token setiap 10 menit.

---

## [1.0.0] — Versi awal

- Proxy dasar dengan single token.
- Endpoint: models, categories, videos, detail, source, download.
