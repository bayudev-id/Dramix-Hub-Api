# MovieBox API Wrapper (Local)

Wrapper API Python untuk layanan MovieBox/oneroom yang dikonversi menjadi REST API lokal menggunakan **FastAPI**. Project ini mendukung pencarian film, detail drama, perolehan link streaming (dengan proxy Referer), dan subtitle dalam satu paket JSON.

## 🚀 Fitur Utama
- **Unified Playback**: Mendapatkan link video dan daftar subtitle dalam satu kali request.
- **Auto-Resolve detailPath**: Cukup masukkan `subjectId`, sistem akan otomatis mencari slug yang diperlukan.
- **Video Proxy**: Dilengkapi dengan proxy internal untuk memintas proteksi *Access Denied* pada CDN video.
- **Search & Discovery**: Mendukung pencarian, saran kata kunci, trending, dan ranking list.
- **Clean Architecture**: Menggunakan Pydantic/Dataclasses untuk model data yang terstruktur.

## 🛠️ Persyaratan
- Python 3.8+
- FastAPI
- Uvicorn
- Requests

Install dependensi:
```bash
pip install fastapi uvicorn requests
```

## 🏁 Cara Menjalankan
Jalankan server menggunakan Uvicorn:
```bash
python app.py
```
Server akan berjalan di `http://localhost:8000`.

## 📖 Dokumentasi Endpoint

### 1. Eksplorasi (Home & Discovery)
| Endpoint | Deskripsi |
| :--- | :--- |
| `GET /raw-home` | Data mentah halaman utama (Banner & Section). |
| `GET /categories` | Daftar genre/kategori film. |
| `GET /trending` | Daftar film yang sedang trending. |

### 2. Pencarian
| Endpoint | Parameter | Deskripsi |
| :--- | :--- | :--- |
| `GET /search` | `keyword`, `page`, `perPage` | Mencari film/drama. |

### 3. Detail & Playback
| Endpoint | Parameter | Deskripsi |
| :--- | :--- | :--- |
| `GET /detail` | `subjectId` atau `detailPath` | Detail lengkap, pemain, & info episode. |
| **`GET /play`** | **`subjectId`**, `season`, `episode` | **Rekomendasi**: Video links + Subtitles. |
| `GET /proxy/video` | `url` | Digunakan secara internal oleh `/play`. |

## 💻 Contoh Penggunaan

### Mencari Film
```bash
curl "http://localhost:8000/search?keyword=Perfect"
```

### Mengambil Link Putar (Terpadu)
Cukup gunakan `subjectId`, sistem akan mengurus sisanya:
```bash
curl "http://localhost:8000/play?subjectId=6524447992693806504&episode=1"
```

### Response Playback Terpadu
```json
{
  "code": 200,
  "data": {
    "streams": [
      {
        "format": "MP4",
        "url": "http://localhost:8000/proxy/video?url=...",
        "resolutions": "720",
        "size": "1089036679"
      }
    ],
    "captions": [
      { "lan": "en", "lan_name": "English", "url": "..." },
      { "lan": "in_id", "lan_name": "Indonesian", "url": "..." }
    ],
    "free_num": 999
  }
}
```

## 📂 Struktur Project
- `app.py`: Entry point FastAPI & rute API.
- `moviebox.py`: Class utama untuk inisialisasi API.
- `api/`: Logika bisnis per kategori (Home, Search, Detail, Play).
- `models/`: Definisi skema data (Dataclasses).
- `core/`: HTTP Client dan penanganan request dasar.

## 📝 Catatan
Endpoint `/play` menggunakan proxy internal untuk menyuntikkan header `Referer` yang diperlukan oleh CDN. Pastikan server tetap berjalan saat memutar video melalui link proxy tersebut.

---
*Dibuat untuk mempermudah integrasi layanan MovieBox ke platform lain.*
