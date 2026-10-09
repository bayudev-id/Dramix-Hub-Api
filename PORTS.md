# DRAMIX GATEWAY - PORT ALLOCATION REGISTRY

Dokumen ini mendefinisikan alokasi port resmi dan standar untuk semua service di ekosistem Dramix.

---

## 1. Port Allocation Table

| Service Name | Engine | Direktori Kerja | Entry Command | Port Default | Env Variable |
|---|---|---|---|---|---|
| **PocketBase** | Go | `pocketbase/` | `pocketbase.exe serve` | **`8090`** | - |
| **CineFlow Hub** | FastAPI | `services/cineflow_hub_api/` | `python main.py` | **`7401`** | `PORT` |
| **WeTV API** | FastAPI | `services/wetv_api/` | `python main.py` | **`7402`** | `PORT` |
| **KissKH API** | Express.js | `services/kisskh_api/` | `node server.js` | **`7403`** | `PORT` |
| **MovieBox API** | FastAPI | `services/moviebox_api/` | `python app.py` | **`7404`** | `PORT` |
| **Viu API** | FastAPI | `services/viu_api/` | `python main.py` | **`7405`** | `PORT` |
| **FreeReels API** | FastAPI | `services/freereels_api/production/` | `python run_proxy.py` | **`7406`** | `PORT` |
| **iQIYI API** | FastAPI | `services/iqiyi_api/production/` | `python run_server.py` | **`7407`** | `PORT` |

---

## 2. Aturan Menambahkan Provider Baru (Next Provider)

Setiap kali Anda menambahkan provider baru di folder `services/provider_nama/`:

1. **Gunakan Port Berurutan Selanjutnya:**
   - Provider ke-9: **`7408`**
   - Provider ke-10: **`7409`**
   - Provider ke-11: **`7410`**, dst.

2. **Gunakan Pattern Konfigurasi Port yang Seragam:**
   - **Python / FastAPI:**
     ```python
     import os
     port = int(os.getenv("PORT", 7408))
     host = os.getenv("HOST", "127.0.0.1")
     uvicorn.run("main:app", host=host, port=port)
     ```
   - **Node.js / Express:**
     ```javascript
     const PORT = process.env.PORT || 7408;
     app.listen(PORT, () => console.log(`Running on port ${PORT}`));
     ```

3. **Daftarkan di PocketBase:**
   - Buka admin PocketBase `http://127.0.0.1:8090/_/`
   - Masukkan ID, nama, icon_url, description, content_type ke koleksi `providers`.

---

## 3. Gateway Endpoint Contract Standards (`:8090`)

Semua client app hanya mengakses Dramix Gateway di port `8090`:

1. **`GET /api/modelles/models`**
   - Mengembalikan daftar provider aktif dari database PocketBase `providers`.
2. **`GET /api/modelles/categories?model_id=<id>`**
   - Mengembalikan daftar kategori yang dinormalisasi (`{ id, name }`) per provider.
3. **`GET /api/modelles/videos?model_id=<id>&category_id=<cat_id>&page=<page>`**
   - Mengembalikan daftar drama/video yang dinormalisasi (`{ id, title, cover, type, source, episode_info, score, views, is_vip, tags }`) per kategori dan halaman.
   - `score`: Rating penonton/IMDb/kritikus (skala 0.0 - 10.0, contoh: `"8.7"`, `"7.6"`, `"0"`).
   - `views`: Total penonton/popularitas/hotness counter (contoh: `"16.3M"`, `"20.9K"`, `"111.6K"`, atau `""` jika tidak ada).
   - Validasi ketat: HTTP 400 untuk parameter invalid/kurang, HTTP 404 untuk provider tak terdaftar, HTTP 403 untuk provider nonaktif.
4. **`GET /api/modelles/detail?model_id=<id>&id=<content_id>`**
   - Mengembalikan informasi detail drama dan struktur season & episode yang dinormalisasi.
   - Format: `{ id, title, cover, description, type, source, release_date, score, views, is_vip, tags, total_episodes, seasons: [{ name, index, total_episodes, episodes: [{ id, title, number, cover, duration_seconds, is_vip, is_express, is_trailer, label, tags }] }] }`
   - Episode Access Tier Parameters:
     - `is_vip`: `true` jika konten membutuhkan langganan VIP, `false` jika gratis atau rental.
     - `is_express`: `true` untuk episode Fast Track / Express.
     - `is_trailer`: `true` untuk cuplikan / trailer / bloopers.
     - `label`: Label status dari upstream (`"VIP"`, `"Sewa"`, `"Fast Track"`, `"Trailer"`, atau `""` jika gratis).
     - `tags`: Array tag status per episode (contoh: `["Sewa"]`, `["VIP"]`, `["Fast Track"]`, `["Trailer"]`, atau `[]` jika gratis).
   - Validasi ketat: HTTP 400 jika query param invalid/kurang, HTTP 404 jika provider tak terdaftar / konten tak ditemukan, HTTP 403 jika provider nonaktif.

5. **`GET /api/modelles/source?model_id=<id>&episode_id=<ep_id>&id=<content_id>`**
   - Mengembalikan daftar stream URL dan subtitle yang dinormalisasi untuk pemutaran video.
   - Parameter Query:
     - `model_id` (Wajib): ID provider (contoh: `youku`, `wetv`, `kisskh`, `moviebox`, `viu`, `freereels`, `iqiyi`).
     - `episode_id` (Wajib): ID episode pemutaran.
     - `id` (Opsional): ID konten/album/series (jika tidak disediakan, fallback ke `episode_id`).
   - Format Respon:
     ```json
     {
       "code": 200,
       "message": "success",
       "data": {
         "id": "content_id",
         "episode_id": "ep_id",
         "duration_seconds": 2698,
         "streams": [
           {
             "quality": "1080p",
             "format": "m3u8",
             "url": "https://...",
             "is_drm": false,
             "drm": null
           }
         ],
         "subtitles": [
           {
             "lang": "id",
             "label": "Bahasa Indonesia",
             "url": "https://..."
           }
         ]
       }
     }
     ```
   - Karakteristik & Aturan:
     - Output JSON deterministik dengan key ordering manual via `e.blob()`: `id` -> `episode_id` -> `duration_seconds` -> `streams` -> `subtitles`.
     - Validasi ketat: HTTP 400 jika ada parameter query tambahan di luar `model_id`, `episode_id`, `id` atau parameter wajib kosong.
     - HTTP 404 jika `model_id` tidak terdaftar, HTTP 403 jika status provider `inactive`.
     - Youku resolution correction: upstream 4K diturunkan menjadi 1080p (`cmfv4hd3` -> 1080p, `cmfv4hd2` -> 720p, `cmfv4hd` -> 480p, `cmfv4sd` -> 360p).

6. **`POST & GET /api/modelles/search`**
   - Mencari konten drama, anime, film, dan saluran live TV di seluruh 24 provider.
   - Mendukung format body POST (CineFlow Hub style):
     ```json
     {
       "model_id": "moviebox",
       "content_type": "movie_tv",
       "page": 1,
       "q": "money"
     }
     ```
   - Dan query param GET:
     `GET /api/modelles/search?model_id=moviebox&q=money&page=1&content_type=movie_tv`
   - Parameter Request:
     - `model_id` (Wajib): ID provider (contoh: `moviebox`, `youku`, `wetv`, `viu`, `freereels`, `iqiyi`).
     - `q` (Wajib): Kata kunci pencarian.
     - `page` (Opsional, default: `1`): Nomor halaman (integer >= 1).
     - `content_type` (Opsional): Tipe konten (`short_drama`, `movie_tv`, `live_tv`). Otomatis ditentukan dari metadata provider jika tidak diisi.
   - Format Respon Baku:
     ```json
     {
       "code": 200,
       "message": "success",
       "data": {
         "model_id": "moviebox",
         "q": "money",
         "page": 1,
         "items": [
           {
             "id": "money-heist-8UcoFG3Uog",
             "title": "Money Heist S1-S5",
             "cover": "https://...",
             "type": "drama",
             "source": "MovieBox",
             "episode_info": "2017-05-02",
             "score": "8.2",
             "views": "",
             "is_vip": false,
             "tags": ["Tindakan", "Kejahatan", "Drama"]
           }
         ]
       }
     }
     ```
   - Karakteristik & Aturan:
     - Output JSON deterministik dengan key ordering manual via `e.blob()`:
       Envelope: `code` -> `message` -> `data`
       Data: `model_id` -> `q` -> `page` -> `items`
       Item: `id` -> `title` -> `cover` -> `type` -> `source` -> `episode_info` -> `score` -> `views` -> `is_vip` -> `tags`.
     - Validasi ketat: HTTP 400 jika ada parameter tambahan di query atau body di luar `model_id`, `q`, `page`, `content_type`, atau jika `model_id` / `q` kosong.
     - HTTP 404 jika `model_id` tidak terdaftar di koleksi `providers`.
     - HTTP 403 jika status provider `inactive`.
     - Dukungan penuh 24 provider: 10 Short Drama (NetShort, Melolo, MoboReels, ShortWave, DramaBoxBaru, ShortMax, ReelShort, StarDustTV, DramaRush, FreeReels), 13 Movie/TV/Anime (Anichin, Anichin V2, Samehadaku, Animelovers, Mobinime, Bstation, Youku, CineMovies, MovieBox, KissKH, Viu, WeTV, iQIYI), dan 1 Live TV (CineTv).
