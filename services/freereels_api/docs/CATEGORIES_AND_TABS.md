# FreeReels - Kategori & Tabs Homepage

## Base Endpoint
```
GET /frv2-api/homepage/v2/tab/index
```

## Tab Keys (Homepage Categories)

| Tab Key | Nama (ID) | Nama (EN) | Deskripsi |
|---------|-----------|-----------|-----------|
| `503` | **Populer** | Popular | Drama paling banyak ditonton |
| `505` | **Baru** | New Released | Drama baru rilis |
| `547` | **Anime** | Anime | Drama animasi |
| `516` | **Dubbing** | Dubbing | Drama dengan sulih suara |
| `501` | **Pria** | Male | Drama untuk audience pria |
| `504` | **Wanita** | Female | Drama untuk audience wanita |
| `622` | **Coming Soon** | Coming Soon | Drama yang akan datang |
| `1001` | ? | ? | (Unknown) |
| `1002` | ? | ? | (Unknown) |

## Module Types per Tab

Setiap tab berisi beberapa **module** (bagian konten). Contoh struktur:

### Tab 503 (Populer)
```json
{
  "items": [
    {
      "type": "recommend",
      "module_name": "Pilihan Populer",
      "module_key": "1036",
      "items": [...]  // 10 drama
    }
  ]
}
```

### Tab 505 (Baru)
```json
{
  "items": [
    {
      "type": "recommend",
      "module_name": "New",
      "module_key": "1040",
      "items": [...]  // 10 drama
    }
  ]
}
```

### Tab 516 (Dubbing)
```json
{
  "items": [
    {
      "type": "recommend",
      "module_name": "Dubbing",
      "module_key": "1065",
      "items": [...]  // 10 drama
    }
  ]
}
```

## Module Keys (Sub-kategori)

| Module Key | Nama | Tipe | Belongs to Tab |
|------------|------|------|----------------|
| `1036` | Pilihan Populer | recommend | 503 (Populer) |
| `1040` | New | recommend | 505 (Baru) |
| `1065` | Dubbing | recommend | 516 (Dubbing) |
| `2204` | (Anime) | recommend | 547 (Anime) |

## Ranking Endpoints

Untuk ranking/leaderboard:

```
POST /frv2-api/homepage/rank
```

**Module Types untuk Ranking:**
- `daily` - Ranking Harian
- `weekly` - Ranking Mingguan
- `monthly` - Ranking Bulanan
- `annually` - Ranking Tahunan

## Drama List Structure

Setiap item drama di homepage feed memiliki:

```json
{
  "key": "QCJvQG2LLD",
  "cover": "https://static-v1.mydramawave.com/...",
  "title": "Master Judi Jadi Suami Rumah Tangga(Sulih Suara)",
  "desc": "Deskripsi drama...",
  "tag": ["Gratis"],
  "content_tags": ["Balas Dendam", "Miskin Jadi Kaya"],
  "operation_tags": [
    {
      "text": "Dubbing",
      "text_color": "#FFFFFF",
      "bg_start": "#F47040",
      "bg_end": "#F52067",
      "tag_type": "dubbed"
    }
  ],
  "episode_count": 61,
  "follow_count": 109710,
  "view_count": 0,
  "episode_info": {
    "id": "LJ5YLRyTpX",
    "cover": "...",
    "external_audio_h264_m3u8": "https://video-v6.mydramawave.com/..."
  }
}
```

## Content Tags (Genre/Tema)

Drama dikategorikan dengan **content_tags**:

### Tema Umum
- `Balas Dendam` - Revenge
- `Miskin Jadi Kaya` - Rags to Riches
- `Identitas Rahasia` - Hidden Identity
- `Teka-Teki Identitas` - Identity Mystery
- `Kesempatan Kedua` - Second Chance
- `Musuh Jadi Kekasih` - Enemies to Lovers
- `Dimanjakan` - Spoiled
- `Kebetulan Manis` - Sweet Coincidence
- `Cinta Setelah Nikah` - Love After Marriage
- `Glow Up` - Transformation

### Kategori Utama (dari series_tag)
- **Romansa**: Romansa, Romansa Kantor, Romansa Gelap, Romansa Kampus
- **Drama**: Drama, Drama Medis
- **Aksi**: Aksi, Ketegangan
- **Fantasi**: Fantasi, Fiksi Ilmiah
- **Komedi**: Komedi
- **Bisnis**: Bisnis

### Sub-kategori Spesifik
- Pernikahan: Pernikahan Kontrak, Pernikahan Cepat, Hubungan Palsu
- Identitas: Identitas Tersembunyi, Identitas Salah, Teka-Teki Identitas
- Hubungan: Bayi Rahasia, Ibu Pengganti, Hubungan Satu Malam, Cinta Terlarang
- Status: Miliarder, CEO/Bos, Dokter, Mahasiswa, Pewaris
- Karakter: Pahlawan Wanita Kuat, Bangkit si Lemah, Dari Miskin ke Kaya

## Operation Tags (Visual Labels)

Tag visual yang muncul di cover drama:

```json
{
  "text": "Dubbing",
  "text_color": "#FFFFFF",
  "bg_start": "#F47040",
  "bg_end": "#F52067",
  "tag_type": "dubbed"
}
```

**Tag Types:**
- `dubbed` - Drama dengan sulih suara
- `popular` - Drama populer (trending)
- `new` - Drama baru
- `free` - Drama gratis
- `vip` - Butuh VIP

## Pagination

Request parameters untuk load more:
- `tab_key`: ID tab (503, 505, dll)
- `position_index`: Posisi scroll (0 = awal, 10000 = bawah)
- `rec_trigger`: Trigger rekomendasi (0 atau 1)

## Search Tabs

Endpoint untuk kategori search:
```
GET /frv2-api/search/audio-tabs
```

Response:
```json
{
  "list": [
    {
      "tab_key": "mix",
      "name": "Mix"
    },
    {
      "tab_key": "dubbed",
      "name": "Dubbing"
    }
  ]
}
```

## Drama Detail Endpoint

Untuk detail lengkap drama (aktor, episode, dll):

```
GET /frv2-api/drama/info_v2
```

**Parameters:**
- `series_id`: Drama ID (dari field `key` di list)
- `scene`: Scene identifier (usually `"1"`)

**Response includes:**
- `name`: Judul drama
- `desc`: Deskripsi
- `episode_count`: Total episode
- `view_count`: Total views
- `follow_count`: Total followers
- `comment_count`: Total comments
- `content_tags`: Array genre/tema
- `episode_list[]`: Array semua episode dengan HLS URL

**Note:** Field `actor` atau `cast` **TIDAK ADA** di response. API tidak menyediakan informasi aktor.

## Flow User Browsing

```
1. Homepage → GET /homepage/v2/tab/index?tab_key=503
   ├─ Lihat list drama populer
   └─ Pagination: position_index=10000 untuk load more

2. Pilih Drama → GET /drama/info_v2?series_id={key}&scene=1
   ├─ Baca deskripsi, tags, episode_count
   ├─ Lihat view_count, follow_count, comment_count
   └─ Browse episode_list

3. Pilih Episode → Langsung play dari HLS URL
   ├─ external_audio_h264_m3u8 (H.264)
   └─ external_audio_h265_m3u8 (H.265)

4. (Optional) Comment → POST /content/comment/save

5. (Optional) Like → POST /drama/episode/like

6. (Optional) Follow → POST /drama/follow
```

## Example: Fetch Populer + Detail

```python
from freereels_client import FreeReelsClient

client = FreeReelsClient()
client.login_anonymous()

# 1. Get popular dramas
popular = client._request("GET", "/frv2-api/homepage/v2/tab/index", 
                         params={"tab_key": "503", "position_index": "0"})

dramas = popular["items"][0]["items"]  # First module's items

# 2. Get first drama detail
drama_key = dramas[0]["key"]
detail = client._request("GET", "/frv2-api/drama/info_v2",
                        params={"series_id": drama_key, "scene": "1"})

info = detail["info"]
print(f"Title: {info['name']}")
print(f"Description: {info['desc']}")
print(f"Episodes: {info['episode_count']}")
print(f"Views: {info['view_count']}")
print(f"Followers: {info['follow_count']}")
print(f"Tags: {', '.join(info['content_tags'])}")

# 3. Get episode HLS URL
episodes = info["episode_list"]
first_ep = episodes[0]
hls_url = first_ep["external_audio_h264_m3u8"]
print(f"Play URL: {hls_url}")
```

## Limitations

1. **Tidak ada endpoint untuk list semua kategori** — tab keys hardcoded (503, 505, 516, etc)
2. **Tidak ada informasi aktor/cast** — field tidak tersedia di API
3. **Module keys tidak terdokumentasi** — hanya bisa ditemukan via reverse engineering
4. **Pagination tidak offset-based** — menggunakan `position_index` yang tidak jelas rumusnya

## Related Endpoints

- `/search/drama` - Search drama by keyword
- `/drama/v3/follow_list` - User's following list
- `/drama/v3/view_history` - Watch history
- `/drama/book-list` - Bookmarked dramas
- `/homepage/rank` - Drama rankings
- `/homepage/user_latest_view_series` - Continue watching
