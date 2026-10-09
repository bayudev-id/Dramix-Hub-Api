# 🎬 WeTV Web API (Python)

Backend API yang mengambil konten streaming dari WeTV menggunakan cookie VIP dari database Supabase. Tidak ada sistem login di sisi ini — autentikasi dan auto-heal cookie ditangani oleh [Node.js Worker](../WeTV_Web_Login_(NodeJS)) secara terpisah.

---

## 📁 Struktur Proyek

```text
├── main.py            # Entry point FastAPI + Bearer Auth middleware
├── home.py            # Router: Beranda, kategori, section
├── search.py          # Router: Pencarian real-time
├── album.py           # Router: Detail album & daftar episode
├── play.py            # Router: Stream resolver VIP (LD → FHD + subtitle VTT)
├── encryption.py      # cKey generator untuk getvinfo API
├── sections.json      # Konfigurasi section beranda
├── vercel.json        # Konfigurasi deploy Vercel (region: sin1)
├── requirements.txt   # Dependencies Python
└── .env               # Variabel environment (TIDAK masuk git)
```

---

## 🔒 Keamanan

| Lapisan | Keterangan |
|---------|------------|
| **Bearer Auth** | Semua endpoint `/api/wetv/*` dilindungi `Authorization: Bearer <API_SECRET_KEY>` (aktif hanya jika `API_SECRET_KEY` diisi di `.env`) |
| **Swagger Disabled** | `/docs`, `/redoc`, `/openapi.json` dinonaktifkan saat `DEBUG=False` |
| **Root 404** | Mengunjungi `/` mengembalikan 404 untuk menyembunyikan eksistensi server |
| **CORS Terbatas** | Hanya origin yang terdaftar di `ALLOWED_ORIGINS` yang diizinkan |
| **Cookie Tidak Bocor** | Response API hanya berisi stream URL & subtitle, bukan raw cookies |

---

## ⚙️ Environment Variables (`.env`)

```env
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJ...                    # Service role key (RAHASIA)
API_SECRET_KEY=                        # Kosongkan untuk dev, isi untuk production
DEBUG=False
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

---

## 🚀 API Endpoints

Semua endpoint berada di bawah `/api/wetv/`.

| Method | Endpoint | Keterangan |
|--------|----------|------------|
| `GET` | `/api/wetv/channel/{id}` | Beranda / kategori konten |
| `GET` | `/api/wetv/categories` | Daftar kategori |
| `GET` | `/api/wetv/sections` | Section beranda |
| `GET` | `/api/wetv/languages` | Bahasa yang didukung |
| `GET` | `/api/wetv/search?query=...` | Pencarian drama |
| `GET` | `/api/wetv/album/{cid}` | Detail album & episode |
| `GET` | `/api/wetv/album/{cid}/clips` | Clip / BTS / trailer |
| `GET` | `/api/wetv/play/{cid}/{vid}` | **Stream VIP** (HLS m3u8 + subtitle VTT) |

---

## 🏃 Cara Menjalankan

```bash
# Install dependencies
pip install -r requirements.txt

# Jalankan server
python main.py
# Server berjalan di http://127.0.0.1:1234
```

---

## ☁️ Deploy ke Vercel

```bash
vercel
```

Pastikan environment variables sudah diset di dashboard Vercel → Settings → Environment Variables.
Region: **Singapore (`sin1`)**.
