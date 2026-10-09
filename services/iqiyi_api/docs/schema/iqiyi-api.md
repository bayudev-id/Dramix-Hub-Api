# Schema: iQIYI Catalog & VIP Metadata REST API

**Source:** docs/prd/iqiyi-api.md
**Database:** Local JSON (v1.0.0) → PostgreSQL/Supabase (v1.1.0+)

## Overview

Dokumen ini merancang skema penyimpanan sesi autentikasi iQIYI untuk server REST API. Pada v1.0.0, sesi login dan cookie disimpan dalam file JSON lokal (`data/sessions.json`) untuk validasi cepat tanpa network overhead. Saat upgrade ke v1.1.0, file JSON akan dimigrasikan ke PostgreSQL via Supabase REST API untuk persistensi multi-instance dan manajemen sesi terdistribusi.

---

## Entities

### iqiyi_session

**Serves:** User Story #1 "lakukan autentikasi via `/api/auth/login` untuk mendapatkan session cookie aktif" dan User Story #2 "cek status sesi aktif via `/api/auth/status`"

**Storage (v1.0.0):** File JSON lokal `data/sessions.json`, struktur top-level `"active_session": { ... }`

**Storage (v1.1.0+):** Tabel PostgreSQL `public.iqiyi_sessions`

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| id | uuid | no | `gen_random_uuid()` (v1.1+) | Primary key, set manually to `uuid.uuid4()` saat JSON creation (v1.0) |
| account_identifier | text | no | - | Nomor HP / email yang digunakan untuk login (e.g., `85161230944`), unik per sesi aktif |
| auth_cookie | text | no | - | String raw cookie gabungan dari response iQIYI Passport (e.g., `QC005=...; P00001=...; ...`) |
| cookie_data | jsonb / object | no | `{}` | Parsed key-value cookie untuk akses mudah dari client (e.g., `{"QC005": "...", "P00001": "...", "qyid": "..."}`) |
| device_id | text | no | - | Device ID terikat saat login (dari Burp capture: `f66426a8bfcb12539fd50c78108494491102`), konsisten per login |
| vip_status | boolean | no | `false` | Apakah akun memiliki status VIP aktif hasil response login |
| vip_type | text | yes | `null` | Label tipe VIP jika ada (e.g., `"Standard VIP"`, `"Premium VIP"`), null jika non-VIP |
| vip_expires_at | timestamptz | yes | `null` | Tanggal kedaluwarsa status VIP jika terdeteksi di response / dari parsing metadata, null jika non-VIP atau tidak diketahui |
| is_active | boolean | no | `true` | Apakah sesi ini sesi aktif yang sedang digunakan server (support future multi-account dengan flag ini) |
| last_validated_at | timestamptz | yes | `null` | Waktu terakhir kali cookie divalidasi ke upstream iQIYI API (untuk detection cookie expiry), null jika belum pernah divalidasi |
| created_at | timestamptz | no | `now()` | Waktu sesi dibuat / login berhasil |
| updated_at | timestamptz | no | `now()` | Waktu sesi terakhir diperbarui / di-refresh oleh client saat re-login |

---

## Relationships

Not applicable (v1.0.0). Hanya ada satu entitas, tidak ada foreign key. Jika pada v1.1.0+ ditambah user registry atau audit log, relasi akan didefinisikan ulang.

---

## Indexes

**v1.0.0 (Local JSON):** Not applicable — pencarian linear atas single object dalam file.

**v1.1.0+ (PostgreSQL/Supabase):**

| Table | Columns | Type | Rationale |
|---|---|---|---|
| iqiyi_sessions | (is_active) | btree | Fast fetch active session saat server startup: `SELECT * FROM iqiyi_sessions WHERE is_active = true LIMIT 1` |
| iqiyi_sessions | (account_identifier) | btree | Upsert/lookup saat login baru: `SELECT * FROM iqiyi_sessions WHERE account_identifier = ? LIMIT 1` |

---

## Constraints

**v1.0.0 (Local JSON):** Validasi aplikatif di Python (`src/client/session_store.py`)

**v1.1.0+ (PostgreSQL/Supabase):**

| Table | Constraint | Type | Definition |
|---|---|---|---|
| iqiyi_sessions | account_identifier unik | unique | `UNIQUE(account_identifier)` — satu akun hanya punya satu row sesi aktif; login baru akan trigger UPDATE (upsert), bukan INSERT |
| iqiyi_sessions | auth_cookie wajib | not null | `NOT NULL` — tidak boleh ada row tanpa cookie autentikasi |
| iqiyi_sessions | is_active flag | check | `is_active IN (true, false)` — nilai hanya boolean (optional, tergantung implementasi) |
| iqiyi_sessions | vip_status konsisten | check | Jika `vip_status = true`, maka `vip_type` harus NOT NULL (optional, validasi aplikatif di v1.0) |

---

## Data Format Examples

### v1.0.0: File JSON (`data/sessions.json`)

```json
{
  "active_session": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "account_identifier": "85161230944",
    "auth_cookie": "QC005=f588c8f70ff477b8f9d941f8b80b9fd3; P00001=xxxxxxxxxxxx; qyid=f66426a8bfcb12539fd50c78108494491102",
    "cookie_data": {
      "QC005": "f588c8f70ff477b8f9d941f8b80b9fd3",
      "P00001": "xxxxxxxxxxxx",
      "qyid": "f66426a8bfcb12539fd50c78108494491102"
    },
    "device_id": "f66426a8bfcb12539fd50c78108494491102",
    "vip_status": true,
    "vip_type": "Premium VIP",
    "vip_expires_at": "2026-11-06T03:06:32Z",
    "is_active": true,
    "last_validated_at": "2026-10-06T04:06:00Z",
    "created_at": "2026-10-06T03:00:00Z",
    "updated_at": "2026-10-06T04:06:32Z"
  }
}
```

### v1.1.0+: PostgreSQL Row

```sql
INSERT INTO iqiyi_sessions (
  id, account_identifier, auth_cookie, cookie_data, device_id,
  vip_status, vip_type, vip_expires_at, is_active, last_validated_at,
  created_at, updated_at
) VALUES (
  '550e8400-e29b-41d4-a716-446655440000'::uuid,
  '85161230944',
  'QC005=f588c8f70ff477b8f9d941f8b80b9fd3; P00001=...; qyid=...',
  '{"QC005": "f588c8f70ff477b8f9d941f8b80b9fd3", "P00001": "...", "qyid": "..."}'::jsonb,
  'f66426a8bfcb12539fd50c78108494491102',
  true,
  'Premium VIP',
  '2026-11-06T03:06:32Z'::timestamptz,
  true,
  '2026-10-06T04:06:00Z'::timestamptz,
  '2026-10-06T03:00:00Z'::timestamptz,
  '2026-10-06T04:06:32Z'::timestamptz
);
```

---

## Migration Notes

### v1.0.0 Implementation

1. **File location:** `data/sessions.json` (gitignore, tidak dicommit).
2. **Initialization:** Server startup membaca file; jika tidak ada atau empty, object `active_session` diinisialisasi sebagai `null` atau `{}`.
3. **Lifecycle:**
   - Saat `POST /api/auth/login` berhasil: parse response iQIYI, populate fields, **write to** `data/sessions.json`.
   - Saat `GET /api/auth/status`: read dari `data/sessions.json`, return status.
   - Saat login request upstream gagal: return error 401 tanpa mengubah file.
4. **Session file locking:** File I/O tidak concurrent-safe di v1.0 (single-instance assumption). Implementasi dapat menambah file lock / WAL jika dibutuhkan.

### v1.1.0+ Migration to Supabase

1. **Pre-migration:**
   - Buat tabel `iqiyi_sessions` di Supabase via console atau migration SQL.
   - Enable Row Level Security (RLS) atau simple auth policy.

2. **Migration script:**
   ```python
   # Pseudocode: read JSON, insert to Supabase
   with open('data/sessions.json', 'r') as f:
       session = json.load(f).get('active_session')
   
   if session:
       supabase.table('iqiyi_sessions').upsert([session]).execute()
   ```

3. **Cutover:** Update `SessionStore` class untuk `read()` dari Supabase REST API instead of JSON file.
4. **Cleanup:** Hapus `data/sessions.json` setelah cutover verified.

### Expand/Contract Considerations

- Jika field baru ditambah di v1.1.0 (e.g., `refresh_token_at`), migration harus:
  1. (Expand) Tambah kolom `refresh_token_at` ke PostgreSQL dengan default `NULL`.
  2. (Migrate) Copy data lama ke tabel staging, transform, insert ke tabel baru.
  3. (Contract) Rename tabel, drop tabel lama.

---

## Open Questions

1. **Cookie encryption in transit:** Apakah cookie perlu di-encrypt sebelum disimpan lokal, atau plain-text cukup karena file `data/sessions.json` sudah di-gitignore? (Rekomendasi: plain-text v1.0, encrypt v1.1 jika multi-user shared server).
2. **Device fingerprint validation:** Apakah server perlu re-validate `device_id` pada setiap request, atau cukup saat login? (Rekomendasi: cukup saat login v1.0, tambah pada v1.1+ if suspicious activity detected).
3. **VIP metadata extraction:** Apakah response iQIYI Passport langsung contain `vip_type` dan `vip_expires_at`, atau perlu API call terpisah ke `/v1/user/info` untuk ekstrak field ini? (Action item: probe Burp capture lebih lanjut).
4. **Session timeout handling:** Berapa lama cookie dianggap "stale" sebelum perlu re-login? (Rekomendasi: 7 hari atau sesuai iQIYI default, set di konstanta v1.0, observasi dari Burp response header `Set-Cookie: ...; Max-Age=...`).
