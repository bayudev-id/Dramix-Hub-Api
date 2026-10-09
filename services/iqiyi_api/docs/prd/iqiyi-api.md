# PRD: iQIYI Catalog & VIP Metadata REST API

## Problem Statement

Aplikasi frontend atau consumer backend membutuhkan akses katalog drama, pencarian, feed kategori, serta detail episode dari iQIYI International (`com.iqiyi.i18n`), termasuk konten yang memerlukan hak akses akun VIP. Saat ini belum tersedia API server mandiri yang bersih, teruji, dan stabil. Proyek terdahulu (FreeReels) memiliki utang teknis berupa kompleksitas proxy ganda dan inkonsistensi routing playground yang tidak boleh terulang di implementasi ini.

## Solution

Membangun REST API service mandiri berbasis Python FastAPI (port 7407) dengan pola Direct Client murni (`IQIYIClient`). Service ini menangani autentikasi akun user (nomor HP/email dan password) ke server iQIYI Passport, mengelola dan menyimpan sesi login/cookie VIP ke Supabase (dengan fallback `.env`), serta mengekspos endpoint bersih dan terstandardisasi (`{code, message, data}`) untuk Search, Tabs/Feed, Drama Detail, dan Episode List.

## User Stories

1. Sebagai sistem consumer, saya ingin melakukan autentikasi via `POST /api/auth/login` menggunakan username/nomor HP dan password agar service memiliki session cookie aktif untuk mengakses katalog berbayar/VIP.
2. Sebagai sistem consumer, saya ingin mengecek status sesi aktif via `GET /api/auth/status` untuk memastikan cookie VIP masih valid sebelum melakukan query massal.
3. Sebagai pengguna, saya ingin mencari drama via `POST /api/search` dengan parameter keyword dan pagination (`pg_num`) agar mendapatkan daftar drama yang relevan lengkap dengan cover dan metadata dasar.
4. Sebagai pengguna, saya ingin mengambil daftar tab kategori dan feed beranda via `GET /api/feed` dan `GET /api/tabs` agar dapat menampilkan kurasi drama terpopuler, drama baru, dan kategori lainnya.
5. Sebagai pengguna, saya ingin mengambil rincian drama via `GET /api/drama/{album_id}` agar mendapatkan sinopsis, genre, tag, tahun rilis, dan total episode.
6. Sebagai pengguna, saya ingin mengambil daftar episode via `GET /api/drama/{album_id}/episodes` agar dapat menampilkan seluruh episode yang tersedia beserta status akses (free vs VIP).
7. Sebagai sistem consumer, saya ingin menerima respon terstandarisasi dengan HTTP status code 401 dan pesan informatif saat session cookie kedaluwarsa agar saya dapat memicu proses re-login.

## Objective

Menyediakan backend REST API service berkinerja tinggi, modular, dan terisolasi dari proxy legacy untuk katalog drama iQIYI International. Target kesuksesan v1.0.0 adalah tersedianya service lokal di `http://localhost:7407` yang mampu melayani autentikasi akun VIP, pencarian terpaginasi, feed beranda, dan detail episode drama dengan format respon seragam.

## Technical Decisions

- **Framework & Runtime**: Python 3.10+ dengan FastAPI dan Uvicorn.
- **Port Layanan**: Port default `7407` (terisolasi dari FreeReels 7406).
- **Arsitektur Client**: Direct Client murni tanpa reverse-proxy layer atau endpoint proxy passthrough. Handler route FastAPI langsung berinteraksi dengan singleton `IQIYIClient`.
- **Autentikasi & Passport**:
  - Target endpoint iQIYI: `https://passport.iq.com/intl/reglogin/mobile_login.action`.
  - Enkripsi password dan request signature (`Pass-Sign`, `Sign`, `Qyid`, `qyidv2`, `dfp`) direplikasi dari flow Android client (`hx.w0` dan native signer/capture Burp).
  - Cookie sesi (`QC005`, `P00001`, dll.) disimpan setelah login berhasil.
- **Penyimpanan Sesi (Session Store)**:
  - Utama: Supabase Table (`iqiyi_sessions`) menyimpan `user_id`, `auth_cookie`, `vip_status`, dan `updated_at`.
  - Fallback / Boot: File `.env` lokal untuk kredensial default (`IQIYI_USERNAME`, `IQIYI_PASSWORD`, `SUPABASE_URL`, `SUPABASE_KEY`).
- **Siklus Sesi & Refresh**:
  - v1.0.0 tidak mengimplementasikan auto-refresh token (ditunda ke v2 setelah pattern token renewal diobservasi).
  - Jika request upstream mengembalikan token invalid/expired, service merespon `401 Unauthorized` dengan petunjuk pemicuan `POST /api/auth/login`.
- **Response Format Envelope**:
  Semua response menggunakan struktur standar REST:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": { ... }
  }
  ```
- **Scope Akun**: Single VIP Account untuk v1.0.0.

## Project Structure

    D:\BackEnd\Drama\iQIYI API/
    ├── docs/
    │   └── prd/
    │       └── iqiyi-api.md            -> Dokumen PRD ini
    ├── src/
    │   ├── client/
    │   │   ├── __init__.py
    │   │   ├── iqiyi_client.py         -> Core HTTP client & request builder
    │   │   ├── signer.py               -> Signature & header calculation
    │   │   └── session_store.py        -> Supabase & .env session persistence
    │   ├── models/
    │   │   └── schemas.py              -> Pydantic models & standard envelopes
    │   └── utils/
    │       └── crypto.py               -> RSA/AES password encryptor
    ├── production/
    │   ├── api/
    │   │   ├── __init__.py
    │   │   ├── routes_auth.py          -> Endpoint /api/auth/*
    │   │   ├── routes_catalog.py       -> Endpoint /api/feed, /api/search
    │   │   └── routes_drama.py         -> Endpoint /api/drama/*
    │   ├── main.py                     -> FastAPI application instance
    │   └── run_server.py               -> Runner script (port 7407)
    ├── tests/
    │   ├── test_client.py              -> Mocked & integration client tests
    │   └── test_api.py                 -> Route endpoint integration tests
    ├── frida/
    │   └── bypass-ssl-pinning.js       -> Android SSL pinning bypass script
    ├── .env.example                    -> Template konfigurasi environment
    ├── requirements.txt                -> Python dependencies
    └── CHANGELOG.md                    -> Catatan rilis berbasis SemVer

## Commands

    Install: pip install -r requirements.txt
    Dev:     python production/run_server.py
    Server:  uvicorn production.main:app --host 0.0.0.0 --port 7407 --reload
    Test:    pytest tests/ -v
    Lint:    flake8 src production tests

## Testing Strategy

- **Mocked Unit Tests**: Menguji `signer.py`, `crypto.py`, dan `session_store.py` secara terisolasi tanpa koneksi jaringan eksternal.
- **Contract & Envelope Tests**: Memastikan semua endpoint (`/api/auth/login`, `/api/search`, `/api/feed`, `/api/drama/{id}`) mengembalikan envelope baku `{code, message, data}` dan status HTTP yang tepat.
- **Integration Tests (Live)**: Uji end-to-end bertahap dengan mock credential dan credential test akun iQIYI.
- **Regression Protection**: Endpoint search memvalidasi parameter paginasi (`pg_num`) dan menjamin tidak ada duplikasi data akibat abaian parameter seperti pada bug FreeReels.

## Boundaries

- **Always**:
  - Kembalikan respon dalam envelope `{code, message, data}`.
  - Sanitasi kredensial (password, auth token) agar tidak pernah tercatat di application logs.
  - Tangani request timeout upstream dengan status HTTP 504 / envelope terstruktur, bukan internal 500 mentah.
  - Dokumentasikan setiap perubahan ke `CHANGELOG.md` mengikuti aturan SemVer.
- **Ask first**:
  - Perubahan skema tabel pada database Supabase.
  - Penambahan library eksternal baru ke `requirements.txt`.
  - Perubahan port layanan atau endpoint contract publik.
- **Never**:
  - Menyimpan atau melakukan commit file `.env` atau kredensial akun ke dalam repositori Git.
  - Mengimplementasikan reverse-proxy passthrough mentah (seperti playground FreeReels).
  - Mengubah logika password encryption tanpa verifikasi hasil capture Burp Suite / decompilation.

## Out of Scope

- Ekstraksi streaming direct link (m3u8/mp4) atau decryption DRM Widevine/FairPlay (ditunda ke milestone v2).
- Multi-user account pooling / session rotation multi-VIP.
- Mekanisme automated background token refresh tanpa re-login.
- Web UI Dashboard / Frontend player (fokus murni pada headless REST API).

## Success Criteria

- [ ] File konfigurasi `.env` dan struktur folder project terbentuk rapi.
- [ ] Modul `IQIYIClient` berhasil melakukan handshake dan login via username/password ke `passport.iq.com`.
- [ ] Session cookie aktif tersimpan dan dapat dimuat kembali dari Supabase / `.env`.
- [ ] Endpoint `POST /api/auth/login` berhasil mengotentikasi akun dan mengembalikan status sesi.
- [ ] Endpoint `POST /api/search` mengembalikan hasil pencarian terpaginasi (`pg_num`) yang valid.
- [ ] Endpoint `GET /api/feed` mengembalikan kurasi drama beranda.
- [ ] Endpoint `GET /api/drama/{album_id}` mengembalikan metadata lengkap drama.
- [ ] Endpoint `GET /api/drama/{album_id}/episodes` mengembalikan daftar episode.
- [ ] Server berjalan stabil di port `7407` dan lulus seluruh unit/contract tests.

## Open Questions

1. Format publikasi key RSA untuk enkripsi password di `passport.iq.com` (apakah statis hardcoded di APK atau diambil via endpoint pre-login config).
2. Definisi skema kolom spesifik tabel Supabase (`iqiyi_sessions`) saat proses migrasi database nanti.
