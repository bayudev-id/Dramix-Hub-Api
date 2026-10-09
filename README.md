# Dramix Hub API (Unified Streaming Gateway)

[![PocketBase](https://img.shields.io/badge/Gateway-PocketBase_Go_Runtime-black.svg?logo=pocketbase)](https://pocketbase.io)
[![FastAPI](https://img.shields.io/badge/Services-FastAPI_Python_3.11+-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com)
[![Express](https://img.shields.io/badge/Services-Express_Node.js-lightgrey.svg?logo=express)](https://expressjs.com)
[![Port](https://img.shields.io/badge/Gateway_Port-8090-blue.svg)](http://127.0.0.1:8090)
[![Repository](https://img.shields.io/badge/GitHub-bayudev--id%2FDramix--Hub--Api-black.svg?logo=github)](https://github.com/bayudev-id/Dramix-Hub-Api)

**Dramix Hub API (Gateway)** adalah sistem backend terdistribusi yang berfungsi sebagai **Anti-Corruption Layer (ACL)** dan **API Gateway** untuk ekosistem streaming Dramix. Gateway ini menormalisasi dan mengonsolidasikan lebih dari **24 penyedia konten video** (drama pendek, serial TV, film, anime, dan siaran Live TV) ke dalam format RESTful API terstandarisasi.

Seluruh komunikasi aplikasi mobile (`com.dramix.app`) hanya berinteraksi melalui satu pintu masuk utama pada port **`8090`** (PocketBase), sementara microservice backend bertindak sebagai adaptor upstream independen.

---

## Daftar Isi
- [Arsitektur Sistem](#arsitektur-sistem)
- [Tabel Alokasi Port & Microservices](#tabel-alokasi-port--microservices)
- [Spesifikasi Kontrak Endpoint Gateway (`:8090`)](#spesifikasi-kontrak-endpoint-gateway-8090)
- [Sistem Lisensi VIP & Hardware Binding](#sistem-lisensi-vip--hardware-binding)
- [Panduan Pembelajaran & Pemecahan Masalah (Engineering Guide)](#panduan-pembelajaran--pemecahan-masalah-engineering-guide)
- [Panduan Instalasi & Menjalankan Service](#panduan-instalasi--menjalankan-service)
- [Alat Administrasi Lisensi (CLI)](#alat-administrasi-lisensi-cli)
- [Struktur Direktori Repositori](#struktur-direktori-repositori)
- [Changelog & Riwayat Versi](#changelog--riwayat-versi)

---

## Arsitektur Sistem

```
 ┌────────────────────────────────────────────────────────────┐
 │               Dramix Android Client App                    │
 └─────────────────────────────┬──────────────────────────────┘
                               │ HTTP / JSON (:8090)
 ┌─────────────────────────────▼──────────────────────────────┐
 │             DRAMIX GATEWAY (PocketBase :8090)              │
 │  pb_hooks: Router, ACL, Schema Normalizer, Device Binding  │
 └─────────┬───────┬───────┬───────┬───────┬───────┬───────┬──┘
           │       │       │       │       │       │       │
    ┌──────▼──┐ ┌──▼──┐ ┌──▼──┐ ┌──▼──┐ ┌──▼──┐ ┌──▼──┐ ┌──▼──┐
    │CineFlow │ │WeTV │ │KissKH││MovieBx││ Viu  ││FreeR.││iQIYI │
    │  :7401  │ │:7402│ │:7403│ │:7404 │ │:7405│ │:7406│ │:7407│
    └─────────┘ └─────┘ └─────┘ └──────┘ └─────┘ └─────┘ └─────┘
```

### Karakteristik Desain:
1. **Single Entry Point**: Aplikasi Android hanya memerlukan satu host konfigurasi (`http://127.0.0.1:8090`).
2. **Tanpa Host Stream Relay**: Gateway hanya mengembalikan metadata dan direct URL CDN. Aliran byte media dialirkan langsung dari CDN asal ke client player (menghemat bandwidth server hingga 99%).
3. **Deterministic Output**: Seluruh endpoint menggunakan serialisasi byte stream `e.blob()` untuk menjamin urutan kunci JSON yang konsisten.
4. **Single Unified Python Environment**: Seluruh microservice Python berbagi satu virtual environment terpusat di root (`.venv`), menghemat ruang disk hingga ~85%.

---

## Tabel Alokasi Port & Microservices

| Service Name | Engine | Direktori Kerja | Entry Command | Port | Deskripsi |
|---|---|---|---|---|---|
| **PocketBase** | Go | `pocketbase/` | `pocketbase.exe serve` | **`8090`** | API Gateway & Database Lisensi |
| **CineFlow Hub** | FastAPI | `services/cineflow_hub_api/` | `python main.py` | **`7401`** | Multi-Source Aggregator & Live TV |
| **WeTV API** | FastAPI | `services/wetv_api/` | `python main.py` | **`7402`** | Scraper & Parser WeTV VOD |
| **KissKH API** | Express | `services/kisskh_api/` | `node server.js` | **`7403`** | Parser Drama Asia & Subtitle |
| **MovieBox API** | FastAPI | `services/moviebox_api/` | `python app.py` | **`7404`** | Provider Film & Serial Barat |
| **Viu API** | FastAPI | `services/viu_api/` | `python main.py` | **`7405`** | Scraper Viu Drama & Variety Show |
| **FreeReels API**| FastAPI | `services/freereels_api/` | `python run_proxy.py` | **`7406`** | Parser Drama Pendek Vertikal |
| **iQIYI API** | FastAPI | `services/iqiyi_api/` | `python run_server.py` | **`7407`** | Scraper iQIYI C-Drama & Anime |

---

## Spesifikasi Kontrak Endpoint Gateway (`:8090`)

### 1. Katalog & Konten

#### `GET /api/modelles/models`
Mengembalikan daftar seluruh penyedia konten aktif yang terdaftar di koleksi PocketBase `providers`.

#### `GET /api/modelles/categories?model_id=<id>`
Mengembalikan daftar kategori konten yang dinormalisasi (`[{ id, name }]`) sesuai provider yang dipilih.

#### `GET /api/modelles/videos?model_id=<id>&category_id=<cat_id>&page=<page>`
Mengembalikan feed kartu video dan status pagination:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "model_id": "moviebox",
    "category_id": "trending",
    "page": 1,
    "has_more": false,
    "items": [
      {
        "id": "content-123",
        "title": "Judul Drama",
        "cover": "https://cdn.example.com/cover.jpg",
        "type": "drama",
        "source": "MovieBox",
        "episode_info": "Episode 12",
        "score": "8.9",
        "views": "1.2M",
        "is_vip": false,
        "tags": ["Aksi", "Romansa"]
      }
    ]
  }
}
```

#### `GET /api/modelles/detail?model_id=<id>&id=<content_id>`
Mengembalikan metadata lengkap konten, sinopsis, cast/crew, serta daftar season & episode beserta status tier:
- `is_vip`: `true` jika memerlukan lisensi VIP.
- `label`: Label resmi (`"VIP"`, `"Sewa"`, `"Trailer"`).
- `tags`: Tag klasifikasi akses (`["Sewa"]`, `["VIP"]`).

#### `GET /api/modelles/source?model_id=<id>&episode_id=<ep_id>&id=<content_id>`
Mengembalikan URL direct CDN video stream dan daftar subtitle (VTT/SRT):
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": "content_id",
    "episode_id": "ep_1",
    "duration_seconds": 2700,
    "streams": [
      { "quality": "1080p", "format": "m3u8", "url": "https://..." }
    ],
    "subtitles": [
      { "lang": "id", "label": "Bahasa Indonesia", "url": "https://..." }
    ]
  }
}
```

#### `GET & POST /api/modelles/search`
Mencari konten di seluruh 24 provider secara instan dengan parameter kata kunci `q`, `model_id`, dan `page`.

---

## Sistem Lisensi VIP & Hardware Binding

Gateway mengoperasikan sistem freemium anonim yang terikat dengan perangkat fisik:
1. **Anonim Tanpa Registrasi**: Client mengirimkan hash SHA-256 dari `ANDROID_ID` melalui header `X-Device-Id`.
2. **Kunci Lisensi Entropi Tinggi**: Format `LCN-XXXX-XXXX-XXXX` (~4.7 kuadriliun kombinasi).
3. **Pencegahan Berbagi Akun**: Lisensi yang telah aktif terkunci ke `device_id` pertama yang mengklaimnya. Upaya aktivasi pada perangkat lain akan ditolak dengan respons HTTP `409 Conflict`.

### Endpoint Lisensi:
- **`POST /api/license/activate`**: Aktivasi kode lisensi `{ "license_key": "LCN-...", "device_id": "..." }`.
- **`GET /api/license/status?device_id=...`**: Memeriksa status VIP dan tanggal kedaluwarsa.
- **`POST /api/license/admin/generate`**: Membuat lisensi baru (otorisasi Bearer token admin).

---

## Panduan Pembelajaran & Pemecahan Masalah (Engineering Guide)

Berikut adalah ringkasan tantangan teknis backend dan bagaimana perbaikannya diterapkan:

1. **Masalah Infinite Scroll Loop pada Provider Tertentu (MovieBox)**:
   - *Akar Masalah*: Gateway mengasumsikan respons upstream selalu paginated. Field `pager.has_more` yang tidak bertipe boolean membuat gateway salah mengembalikan `has_more: true` ke mobile app.
   - *Solusi*: Terapkan validasi `typeof res.json.pager.has_more === "boolean"` dan setel *safe default* `has_more = false`.
2. **Normalisasi Data 24 Provider (ACL Pattern)**:
   - *Solusi*: Seluruh perbedaan upstream diserap di layer `pb_hooks` sehingga client Android tidak terikat pada perubahan struktur API pihak ketiga.
3. **Determinisme Serialisasi JSON**:
   - *Solusi*: Menggunakan `e.blob()` dan string concatenation untuk memastikan urutan field JSON tetap konsisten dan aman untuk hashing / signature.

> 📘 **Pelajari Selengkapnya**: Ulasan mendalam, diagram, dan panduan arsitektur tersedia di [`docs/TROUBLESHOOTING_AND_LEARNING_GUIDE.md`](docs/TROUBLESHOOTING_AND_LEARNING_GUIDE.md).

---

## Panduan Instalasi & Menjalankan Service

### 1. Prasyarat
- **Python**: Versi 3.10 atau 3.11+.
- **Node.js**: Versi 18 atau 20 LTS.
- **PocketBase**: Binary Windows `pocketbase.exe` atau binary Linux pada folder `pocketbase/`.

### 2. Setup Virtual Environment Terpadu
```powershell
# Buat virtual environment di root
python -m venv .venv

# Aktifkan virtual environment
.\.venv\Scripts\Activate.ps1

# Instal seluruh dependensi microservices
pip install -r requirements.txt

# Instal dependensi KissKH API (Node.js)
cd services/kisskh_api
npm install
cd ../..
```

### 3. Menjalankan Seluruh Service Sekaligus
Gunakan skrip master launcher di lingkungan Windows:
```cmd
start_all.bat
```
Atau matikan semua service:
```cmd
stop_all.bat
```

### 4. Menggunakan Process Manager (PM2 / Linux)
```bash
pm2 start ecosystem.config.js
pm2 status
```

---

## Alat Administrasi Lisensi (CLI)

Tersedia skrip administrasi PowerShell `license-admin.ps1` untuk mengelola lisensi pengguna:

```powershell
# 1. Generate lisensi baru (default paket VIP 30 hari)
.\license-admin.ps1 -Action generate -Plan "VIP" -Days 30

# 2. Generate multi-license (contoh: 5 lisensi)
.\license-admin.ps1 -Action batch -Count 5 -Days 30

# 3. Melihat daftar lisensi aktif
.\license-admin.ps1 -Action list -Status active

# 4. Mencabut (revoke) lisensi
.\license-admin.ps1 -Action revoke -Key "LCN-XXXX-XXXX-XXXX"
```

---

## Struktur Direktori Repositori

```
Dramix_Gateway/
├── docs/                   # Laporan implementasi & panduan teknis
├── pocketbase/
│   ├── pb_hooks/           # Logic router, proxy, normalisasi, dan lisensi
│   ├── pb_migrations/      # Skema database SQLite (providers, licenses)
│   └── .env.example        # Contoh konfigurasi environment
├── services/               # Microservices provider independen
│   ├── cineflow_hub_api/   # Multi-source scraper (FastAPI)
│   ├── wetv_api/           # WeTV scraper (FastAPI)
│   ├── kisskh_api/         # KissKH scraper (Express)
│   ├── moviebox_api/       # MovieBox scraper (FastAPI)
│   ├── viu_api/            # Viu scraper (FastAPI)
│   ├── freereels_api/      # FreeReels vertical reels scraper (FastAPI)
│   └── iQIYI_api/          # iQIYI scraper (FastAPI)
├── ecosystem.config.js     # Konfigurasi PM2 Process Manager
├── license-admin.ps1       # CLI generator lisensi VIP
├── PORTS.md                # Registri resmi alokasi port
├── requirements.txt        # Dependensi Python terpadu
├── start_all.bat           # Master startup script
├── stop_all.bat            # Master shutdown script
├── README.md               # Dokumentasi utama proyek
└── CHANGELOG.md            # Catatan riwayat perubahan
```

---

## Changelog & Riwayat Versi

Lihat catatan lengkap pembaruan fitur, perbaikan bug, dan migrasi skema di [CHANGELOG.md](CHANGELOG.md).

---

## Repositori & Lisensi

- **Repository**: [https://github.com/bayudev-id/Dramix-Hub-Api](https://github.com/bayudev-id/Dramix-Hub-Api)
- **Maintainer**: Bayu Dev (`Dramix Ecosystem`)
