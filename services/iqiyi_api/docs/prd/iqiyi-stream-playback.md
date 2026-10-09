# PRD: iQIYI Video Stream & Subtitle Delivery API (v2.0.0)

## Problem Statement

Pada rilis v1.0.0, API telah sukses menyediakan metadata katalog lengkap (pencarian drama, tab navigasi, feed trending, detail drama, dan daftar episode hingga penandaan status VIP). Namun, konsumen API (aplikasi frontend web, mobile, atau video player) belum dapat memutar video karena tidak tersedianya endpoint playback yang menghasilkan URL stream video aktual (M3U8 / TS / MPD) dan file subtitle terjemahan yang siap dikonsumsi player.

## Solution

Menyediakan endpoint playback mandiri `GET /api/play/{tv_id}` (beserta alias `GET /api/drama/{album_id}/episode/{episode_number}/playback`) yang mengekstrak dan mengembalikan daftar direct CDN stream URL berkecepatan tinggi dalam berbagai pilihan kualitas (360p, 480p, 720p, 1080p VIP), daftar audio track (jika tersedia opsi dubbing), dan daftar subtitle track (WebVTT / SRT) secara real-time dari infrastruktur iQIYI dengan otentikasi VIP otomatis.

Seluruh data disajikan dalam model Direct CDN URL tanpa membebani traffic bandwidth server lokal (Mini PC Ubuntu).

## User Stories

1. Sebagai aplikasi client/player, saya ingin memanggil `GET /api/play/{tv_id}` untuk mendapatkan direct URL stream video dari episode yang dipilih sehingga video dapat langsung diputar.
2. Sebagai pengguna gratis, saya ingin dapat memutar episode gratis pada resolusi standar (360p - 720p) tanpa hambatan otentikasi.
3. Sebagai pemilik akun VIP, saya ingin backend otomatis menyertakan sesi VIP aktif sehingga endpoint menghasilkan URL stream resolusi tinggi (1080p / Full HD / VIP Exclusive) untuk episode bertanda VIP.
4. Sebagai aplikasi video player, saya ingin menerima daftar pilihan kualitas stream lengkap (`360p`, `480p`, `720p`, `1080p`) beserta bitrate dan formatnya agar player dapat melakukan adaptive bitrate switching.
5. Sebagai penonton internasional, saya ingin menerima daftar track subtitle lengkap (Bahasa Indonesia, English, dll.) dalam format WebVTT (`.vtt`) atau SRT (`.srt`) langsung agar teks terjemahan dapat ditampilkan di player.
6. Sebagai penonton konten multi-bahasa, saya ingin menerima daftar audio track (Original, Indonesian Dub, dll.) jika drama tersebut menyediakan pilihan dubbing.
7. Sebagai developer frontend, saya ingin opsi memanggil playback menggunakan kombinasi nomor episode `GET /api/drama/{album_id}/episode/{episode_number}/playback` tanpa harus mencari `tv_id` terlebih dahulu.
8. Sebagai pengembang sistem, saya ingin respon error yang informatif dalam envelope `{code, message, data}` jika `tv_id` tidak ditemukan atau sesi akun VIP kedaluwarsa.

## Objective

Membangun kapabilitas media delivery berkecepatan tinggi pada service FastAPI port 7407 yang mengubah `tv_id` episode menjadi paket playback siap putar (Direct CDN Video URLs + Subtitles + Audio Tracks) dengan otentikasi VIP otomatis. Keberhasilan diukur dari kemampuan player eksternal memutar video HD dan menampilkan subtitle bahasa Indonesia/Inggris secara lancar tanpa proxy bandwidth pada server lokal.

## Technical Decisions

- **Primary Endpoint**: `GET /api/play/{tv_id}`
  - Menerima parameter path `tv_id` (ID unik episode/video iQIYI).
  - Parameter query opsional: `bid` (bitrate id preferensi, misal: `500` untuk 720p, `600` untuk 1080p).
- **Secondary Convenience Alias**: `GET /api/drama/{album_id}/episode/{episode_number}/playback`
  - Melakukan lookup internal cepat ke `get_episodes(album_id)` untuk mendapatkan `tv_id` episode terkait, lalu meresolusi playback.
- **Direct CDN Streaming Model**:
  - Backend hanya melakukan handshake/resolving ke upstream dispatch iQIYI (`cache-video.iq.com` / web playback engine).
  - Endpoint mengembalikan direct link URL dari CDN iQIYI (`*.71edge.com` / CDN Oversea).
  - Server Mini PC tidak mengunduh chunk `.ts` maupun mem-proxy aliran byte video.
- **Authentication & VIP Integration**:
  - Backend otomatis membaca cookie aktif (`I00001`, `QC005`, `I00019`) dari `data/sessions.json`.
  - Jika sesi VIP aktif, handshake upstream meminta hak akses VIP stream bitrate tinggi (1080p).
  - Jika tidak ada sesi VIP, playback tetap berfungsi untuk episode/kualitas gratis (fallback publik).
- **Subtitle Handling**:
  - Mengambil daftar subtitle track (`stl`) dari upstream dispatch.
  - Menggabungkan base domain subtitle (`dstl`) dengan path WebVTT (`.vtt`) dan SRT (`.srt`).
  - Mengembalikan metadata bahasa (contoh: `name: "Bahasa Indonesia"`, `lang: "id"`, `format: "webvtt"`, `url: "https://..."`).
- **Standard Envelope Response**:
  - Seluruh respon sukses dibungkus dalam `{ code: 200, message: "success", data: PlaybackData }`.

### Skema Respons Playback (`PlaybackData`)

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "tv_id": "5707911360925900",
    "album_id": "6115411610783301",
    "duration": 2700,
    "is_vip_applied": true,
    "streams": [
      {
        "quality": "1080p",
        "bid": 600,
        "format": "m3u8",
        "url": "https://zlayercdnoversea.inter.71edge.com/...",
        "is_vip": true
      },
      {
        "quality": "720p",
        "bid": 500,
        "format": "m3u8",
        "url": "https://zlayercdnoversea.inter.71edge.com/...",
        "is_vip": false
      }
    ],
    "subtitles": [
      {
        "language": "Bahasa Indonesia",
        "lang_code": "id",
        "format": "webvtt",
        "url": "https://meta.video.iqiyi.com/..."
      },
      {
        "language": "English",
        "lang_code": "en",
        "format": "webvtt",
        "url": "https://meta.video.iqiyi.com/..."
      }
    ],
    "audio_tracks": [
      {
        "name": "Original",
        "lang_code": "zh",
        "is_default": true
      }
    ]
  }
}
```

## Project Structure

    src/
    ├── client/
    │   ├── iqiyi_client.py         -> Core client + modul get_playback()
    │   ├── signer.py               -> Request builder & header signing
    │   └── session_store.py        -> Session JSON persistence
    ├── models/
    │   └── schemas.py              -> Penambahan schema PlaybackInfo, StreamQuality, SubtitleItem
    production/
    ├── api/
    │   ├── routes_playback.py      -> Router endpoint /api/play/{tv_id}
    │   ├── routes_catalog.py       -> Router katalog eksisting v1.0.0
    │   └── routes_auth.py          -> Router auth eksisting v1.0.0
    │   main.py                     -> Registrasi routes_playback
    tests/
    ├── test_playback.py            -> Unit tests mocking upstream dispatch
    └── test_integration.py         -> E2E live test pemutaran video real-time
    docs/prd/
    ├── iqiyi-api.md                -> PRD v1.0.0 (Katalog & Auth)
    └── iqiyi-stream-playback.md    -> PRD v2.0.0 (Stream Playback & Subtitle)

## Commands

    Dev Server:     python production/run_server.py
    Run Tests:      pytest
    Run E2E Only:   pytest tests/test_integration.py -v
    Format / Check: python -m py_compile production/main.py

## Testing Strategy

- **Unit Tests**:
  - Menguji parsing respon stream dispatch (resolusi stream, M3U8 URLs, perakitan subtitle WebVTT/SRT).
  - Menguji penanganan episode VIP vs gratis tanpa koneksi jaringan luar (mocked responses).
- **Integration Tests (E2E Live)**:
  - Menguji endpoint `GET /api/play/5707911360925900` secara live ke server port 7407.
  - Memverifikasi HTTP 200, validitas format URL stream CDN (`.m3u8` / `.ts`), dan keberadaan subtitle track Bahasa Indonesia & Inggris.
  - Memverifikasi HTTP status dan payload yang dapat di-stream langsung oleh video player.

## Boundaries

- **Always**:
  - Menjaga respon dalam format standar `{code, message, data}`.
  - Menggunakan sesi VIP dari `data/sessions.json` jika tersedia.
  - Menjaga model Direct CDN URL (tidak menampung buffer byte video di RAM/disk server).
  - Menjalankan unit test dan E2E test sebelum commit git rilis.
- **Ask first**:
  - Mengubah format envelope atau skema data yang memutus kompatibilitas frontend.
  - Menambahkan dependensi binary berat seperti FFmpeg di server.
- **Never**:
  - Melakukan re-encoding / transcoding video di server backend.
  - Menyimpan file video utuh berhak cipta ke media penyimpanan lokal.
  - Mengabaikan error otentikasi upstream.

## Out of Scope

- Video player UI frontend (aplikasi player diserahkan ke client consumer).
- Bypass DRM level hardware (Widevine L1).
- Server-side caching atau re-hosting file video di VPS/Mini PC.
- Download manager video offline berbasis backend.

## Success Criteria

- [ ] Endpoint `GET /api/play/{tv_id}` aktif dan terdokumentasi di Swagger `/docs`.
- [ ] Endpoint `GET /api/drama/{album_id}/episode/{episode_number}/playback` aktif sebagai alias.
- [ ] Endpoint mengembalikan minimal 1 URL stream video langsung dari CDN iQIYI yang valid dan siap diputar.
- [ ] Tersedia pilihan kualitas video (minimal resolusi standar 720p dan 1080p untuk akun VIP).
- [ ] Daftar subtitle track terisi lengkap dengan URL WebVTT/SRT (termasuk Bahasa Indonesia dan Inggris jika disediakan iQIYI).
- [ ] Seluruh unit test dan integration test baru lolos uji (`pytest` hijau 100%).
- [ ] Pembaruan tercatat di `CHANGELOG.md` di bawah versi `v2.0.0` dan di-commit ke Git repository dengan tag `v2.0.0`.

## Open Questions

- (None saat ini; parameter dispatch dan model direct CDN sudah disepakati).
