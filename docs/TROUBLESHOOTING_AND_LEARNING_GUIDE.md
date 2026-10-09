# Panduan Pemecahan Masalah & Pembelajaran Teknikal Backend (Gateway & APIs)

Dokumen ini mendokumentasikan secara komprehensif akar masalah (*root cause*), diagnosis, solusi implementasi, dan prinsip desain (*architectural patterns*) pada **Dramix Hub API / Gateway**. Dirancang sebagai referensi belajar dan *post-mortem* operasional bagi pengembang.

---

## Daftar Isi
1. [Kasus 1: Normalisasi Pagination & Fallback Defensive (MovieBox Loop)](#kasus-1-normalisasi-pagination--fallback-defensive-moviebox-loop)
2. [Kasus 2: Anti-Corruption Layer (ACL) untuk 24 Provider Beragam](#kasus-2-anti-corruption-layer-acl-untuk-24-provider-beragam)
3. [Kasus 3: Lisensi Freemium Berbasis Hardware Binding Anonim](#kasus-3-lisensi-freemium-berbasis-hardware-binding-anonim)
4. [Kasus 4: Deterministic JSON Key Ordering pada PocketBase Hooks](#kasus-4-deterministic-json-key-ordering-pada-pocketbase-hooks)
5. [Kasus 5: Arsitektur Multi-Service Port Orchestration & Single Unified Environment](#kasus-5-arsitektur-multi-service-port-orchestration--single-unified-environment)

---

## Kasus 1: Normalisasi Pagination & Fallback Defensive (MovieBox Loop)

### Gejala Masalah
Aplikasi mobile mengalami request berulang-ulang tanpa henti (*infinite loop fetch*) saat pengguna menjelajahi kategori tertentu di MovieBox (contoh: kategori drama atau genre spesifik yang hanya memiliki 1 batch konten). Akibatnya, server kebanjiran request dan client menampilkan duplikasi kartu video.

### Akar Masalah (Root Cause)
Pada `pocketbase/pb_hooks/videos.pb.js`, implementasi awal mengasumsikan bahwa seluruh response provider selalu menyertakan metadata pagination yang valid. Jika upstream tidak mengembalikan field `has_more` atau jika nilainya bernilai `null`/`undefined`, variabel lokal tetap bernilai `true`:
```javascript
// BUG SEBELUMNYA:
let hasMore = true;
if (res.json && res.json.pager) {
    hasMore = res.json.pager.has_more ?? true; // Berbahaya! Jika undefined tetap true
}
```

### Cara Mendiagnosis
1. Periksa log PocketBase pada saat endpoint dipanggil:
   ```http
   GET /api/modelles/videos?model_id=moviebox&category_id=popular_movies&page=1
   ```
2. Amati payload upstream dari microservice MovieBox (`:7404`):
   ```json
   {
     "items": [...],
     "pager": { "page": 1, "page_size": 20 } // Tidak ada has_more
   }
   ```
3. Perhatikan respons yang dikeluarkan oleh Gateway ke Android Client:
   `"has_more": true`. Client berasumsi ada halaman 2, mengirim request `page=2`, menerima list kosong atau identik, namun tetap diberitahu `"has_more": true`.

### Solusi & Implementasi
Terapkan **Type-Strict Boolean Check & Non-Trending Cutoff**:
```javascript
// PERBAIKAN DI videos.pb.js:
const isTrending = (String(categoryId) === "3521493905000087296");
if (!isTrending && pageNum > 1) {
    // Kategori selain Rekomendasi tidak memiliki pagination; kembalikan kosong jika page > 1
    hasMore = false;
    rawItems = [];
} else {
    // Fetch ke microservice :7404
    ...
    if (isTrending && res.json && res.json.pager && typeof res.json.pager.has_more === "boolean") {
        hasMore = res.json.pager.has_more;
    } else {
        hasMore = false;
    }
}
```
Untuk MovieBox, hanya kategori khusus (`Rekomendasi` / feed paginated) yang upstream-nya menyertakan pagination dinamis via `pager.has_more`. Seluruh kategori kurasi statis lainnya langsung diputus dengan `has_more: false` pada `pageNum = 1`, dan permintaan `pageNum > 1` langsung mengembalikan array kosong tanpa memanggil upstream kembali.

### Pelajaran Penting (Lessons Learned)
- **Defensive Defaulting**: Pada integrasi multi-source pihak ketiga, default state harus selalu nilai teraman (*safe default*). Pagination default adalah `false`, bukan `true`.
- **Short-Circuit Static Categories**: Untuk seksi data kurasi statis yang tidak mendukung pagination upstream, jangan biarkan query `page > 1` menembus upstream. Potong langsung di API gateway untuk mencegah loop pengiriman data identik dan membuang resource server.
- **Hot-Reload vs Startup Hooks**: Perubahan hook JavaScript pada PocketBase (`pb_hooks/*.js`) dievaluasi saat inisialisasi server. Setelah memperbarui script hook, PocketBase wajib di-restart agar kode baru aktif.
- **Type Checking Primitif**: Jangan hanya memeriksa `truthy/falsy` di JavaScript (`if (pager.has_more)`). Gunakan `typeof ... === "boolean"` untuk membedakan antara `undefined`, `null`, `0`, dan `false`.

---

## Kasus 2: Anti-Corruption Layer (ACL) untuk 24 Provider Beragam

### Tantangan Arsitektur
Dramix mengintegrasikan 24 penyedia konten video dari berbagai platform:
- **10 Short Drama**: NetShort, Melolo, MoboReels, ShortWave, DramaBoxBaru, ShortMax, ReelShort, StarDustTV, DramaRush, FreeReels.
- **13 Movie/TV/Anime**: Youku, WeTV, iQIYI, Viu, MovieBox, KissKH, Anichin, Samehadaku, Animelovers, Mobinime, Bstation, CineMovies, dll.
- **1 Live TV**: CineTv.

Masing-masing provider memiliki struktur data yang sangat berbeda: sebagian menggunakan camelCase, snake_case, format resolusi m3u8 master playlist, direct MP4, hingga token enkripsi DRM kustom. Jika client Android harus menangani variasi ini langsung, aplikasi mobile akan menjadi rapuh dan membengkak.

### Solusi Desain
Dramix Gateway bertindak sebagai **Anti-Corruption Layer (ACL)** murni:
1. Client Android hanya mengetahui 6 endpoint baku di port `8090`:
   - `/api/modelles/models` (Daftar provider)
   - `/api/modelles/categories` (Kategori provider)
   - `/api/modelles/videos` (Daftar video & pagination)
   - `/api/modelles/detail` (Detail konten, season, episode, access tier)
   - `/api/modelles/source` (Direct stream playback URL & subtitle)
   - `/api/modelles/search` (Pencarian global)
2. Normalisasi Data di PocketBase Hook (`pb_hooks/`):
   Setiap respons di-mapping ke format standar:
   - Episode status dinormalisasi menjadi: `is_vip`, `is_express`, `is_trailer`, `label`, `tags`.
   - Rating dan views dinormalisasi menjadi string numerik bersih (`score: "8.7"`, `views: "1.2M"`).
   - Stream video dinormalisasi ke list objek: `{ quality, format, url, is_drm, drm }`.

### Pelajaran Penting (Lessons Learned)
- **Isolasi Perubahan**: Saat salah satu provider mengubah struktur API internalnya, hanya microservice Python/Node terkait atau satu file hook di Gateway yang perlu diubah. Aplikasi Android tidak perlu diperbarui atau di-compile ulang.

---

## Kasus 3: Lisensi Freemium Berbasis Hardware Binding Anonim

### Tantangan Bisnis & Keamanan
Aplikasi tidak mewajibkan registrasi akun dengan email/kata sandi (agar pengalaman pengguna instan tanpa friksi). Namun, bisnis membutuhkan cara untuk:
1. Membatasi pengguna gratis hanya dapat menonton Episode 1–3.
2. Mengizinkan pengguna VIP menonton Episode 4+ dan episode khusus sewa.
3. Mencegah 1 kode lisensi dibagikan ke banyak perangkat berbeda.

### Solusi Implementasi
1. **Device Identification**:
   Aplikasi Android mengirimkan SHA-256 hash dari `ANDROID_ID` perangkat keras pada header `X-Device-Id`.
2. **Database Migration (`pb_migrations`)**:
   Membuat koleksi `licenses` dengan index unik:
   - `license_key` (Format: `LCN-XXXX-XXXX-XXXX`, entropi 12 karakter alfanumerik $\approx 4.7 \times 10^{15}$ kombinasi).
   - `device_id` (Terkunci ke 1 perangkat saat status `active`).
   - `expires_at` (Masa berlaku 30 hari atau sesuai paket).
   - `session_token` (Token acak 64 karakter).
3. **Konflik Hardware**:
   Jika perangkat B mencoba mengaktifkan kode lisensi yang sudah terikat dengan perangkat A, Gateway mengembalikan HTTP `409 Conflict` (*License already bound to another device*).

### Pelajaran Penting (Lessons Learned)
- Anonymous hardware-bound licensing memberikan keseimbangan ideal antara proteksi bisnis terhadap pembajakan dan kenyamanan pengguna tanpa formulir login yang rumit.

---

## Kasus 4: Deterministic JSON Key Ordering pada PocketBase Hooks

### Gejala Masalah
Beberapa klien HTTP pada lingkungan pengujian otomatis mengalami kegagalan validasi hash atau caching saat mem-parsing response JSON karena urutan kunci (*key order*) dalam JSON berubah-ubah antar request.

### Akar Masalah (Root Cause)
Di PocketBase (Go runtime), fungsi helper bawaan `e.json(200, obj)` menggunakan map Go standar yang iterasi kuncinya secara desain dibuat acak (*randomized map traversal*).

### Solusi & Implementasi
Gunakan konstruksi string JSON manual dengan urutan baku dan kirim sebagai byte blob:
```javascript
// Menggunakan e.blob untuk menjaga susunan key JSON:
const jsonString = 
    '{"code":200,"message":"success","data":{' +
    '"id":' + JSON.stringify(id) + ',' +
    '"episode_id":' + JSON.stringify(episodeId) + ',' +
    '"duration_seconds":' + duration + ',' +
    '"streams":' + JSON.stringify(streams) + ',' +
    '"subtitles":' + JSON.stringify(subtitles) +
    '}}';

return e.blob(200, "application/json", jsonString);
```

### Pelajaran Penting (Lessons Learned)
- Jika determinisme JSON dibutuhkan untuk signature hashing, caching layer, atau kepatuhan schema ketat, hindari serialisasi map dinamis. Gunakan serializer dengan key ordering deterministik atau string buffer.

---

## Kasus 5: Arsitektur Multi-Service Port Orchestration & Single Unified Environment

### Tantangan Efisiensi Sumber Daya
Gateway mengoperasikan 8 service secara bersamaan (PocketBase + 7 microservices). Jika setiap service Python memiliki folder `.venv` masing-masing, penggunaan storage lokal dapat membengkak hingga puluhan gigabyte dan pemeliharaan versi dependensi menjadi rumit.

### Solusi Desain
1. **Unified Virtual Environment (`requirements.txt`)**:
   Satu virtual environment terpusat di root (`.venv`) yang mencakup FastAPI, Uvicorn, Pydantic, HTTPX, Requests, Cryptography, dan BeautifulSoup4.
2. **Standard Registry (`PORTS.md`)**:
   Setiap service memiliki alokasi port statis berurutan:
   - `8090`: PocketBase Gateway
   - `7401`: CineFlow Hub
   - `7402`: WeTV API
   - `7403`: KissKH API
   - `7404`: MovieBox API
   - `7405`: Viu API
   - `7406`: FreeReels API
   - `7407`: iQIYI API
3. **Master Launcher (`start_all.bat` & `stop_all.bat`)**:
   Skrip otomatisasi yang mendeteksi virtual environment, menyalakan seluruh service secara terurut dengan timeout proteksi, dan menyediakan skrip pembunuhan proses instan berdasarkan alokasi port.
